import json
import os
import base64
import re
from pathlib import Path
from collections import Counter, deque
import httpx
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Live Vision Backend")

# Allow local dev usage; lock down for prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmotionConfig(BaseModel):
    endpoint: str = ""
    token: str = ""
    model: str = ""


_config_path = Path(os.getenv("EMOTION_CONFIG_PATH", "/data/emotion-config.json"))


def _load_emotion_config() -> EmotionConfig:
    if _config_path.exists():
        try:
            data = json.loads(_config_path.read_text(encoding="utf-8"))
            return EmotionConfig(**data)
        except Exception:
            pass
    return EmotionConfig(
        endpoint=os.getenv("EMOTION_ENDPOINT", "").strip(),
        token=os.getenv("EMOTION_TOKEN", "").strip(),
        model=os.getenv("EMOTION_MODEL", "").strip(),
    )


def _save_emotion_config(config: EmotionConfig) -> None:
    _config_path.parent.mkdir(parents=True, exist_ok=True)
    _config_path.write_text(config.model_dump_json(), encoding="utf-8")


_emotion_config = _load_emotion_config()
_emotion_history = deque(maxlen=12)
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
)


DETAILED_EMOTIONS = {
    "happy",
    "joy",
    "excited",
    "smile",
    "sad",
    "angry",
    "fear",
    "disgust",
    "frustrated",
    "neutral",
}

EMOTION_KEYWORDS = {
    "happy": {"happy", "happiness", "pleased", "content"},
    "joy": {"joy", "joyful", "delighted"},
    "excited": {"excited", "surprised", "surprise", "thrilled"},
    "smile": {"smile", "smiling", "smiley", "grin"},
    "sad": {"sad", "upset", "downcast", "depressed", "unhappy", "frown", "frowning"},
    "angry": {"angry", "anger", "mad", "annoyed", "irritated"},
    "fear": {"fear", "fearful", "afraid", "scared", "anxious", "worried"},
    "disgust": {"disgust", "disgusted", "repulsed", "aversion"},
    "frustrated": {"frustrated", "frustration", "stressed", "tense"},
    "neutral": {"neutral", "calm", "expressionless", "flat"},
}


def _normalize_emotion_detail(label: str) -> str:
    s = label.strip().lower()
    if s in DETAILED_EMOTIONS:
        return s
    if s in {"positive"}:
        return "happy"
    if s in {"negative"}:
        return "sad"
    if s in {"smiling", "smiley"}:
        return "smile"
    if s in {"happiness", "joyful"}:
        return "joy"
    if s in {"surprised", "surprise"}:
        return "excited"
    if s in {"upset", "frown", "frowning", "depressed", "contempt"}:
        return "sad"
    if s in {"anger", "mad"}:
        return "angry"
    if s in {"afraid", "fearful"}:
        return "fear"
    if s in {"frustration"}:
        return "frustrated"
    return "neutral"


def _emotion_bucket(detail: str) -> str:
    if detail in {"happy", "joy", "excited", "smile"}:
        return "positive"
    if detail in {"sad", "angry", "fear", "disgust", "frustrated"}:
        return "negative"
    return "neutral"


def _stabilize_emotion(detail: str) -> str:
    _emotion_history.append(detail)
    recent = list(_emotion_history)[-6:]
    non_neutral = [e for e in recent if e != "neutral"]
    if detail == "neutral" and len(non_neutral) >= 2:
        return Counter(non_neutral).most_common(1)[0][0]
    return detail


def _extract_emotion_detail_from_chat(data: dict) -> tuple[str, str]:
    choices = data.get("choices", [])
    if not choices:
        return "neutral", ""
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        content = " ".join(parts)
    text = str(content)
    token = re.sub(r"[^a-z]", "", text.strip().lower())
    if token:
        normalized = _normalize_emotion_detail(token)
        if normalized in DETAILED_EMOTIONS:
            return normalized, text
    text_l = text.lower()
    scores = {k: 0 for k in DETAILED_EMOTIONS}
    for emotion, words in EMOTION_KEYWORDS.items():
        for word in words:
            if re.search(rf"\b{re.escape(word)}\b", text_l):
                scores[emotion] += 1
    # Prefer explicit non-neutral signals over neutral when both appear.
    non_neutral = {k: v for k, v in scores.items() if k != "neutral"}
    best_non_neutral = max(non_neutral, key=non_neutral.get)
    if non_neutral[best_non_neutral] > 0:
        return best_non_neutral, text
    if scores["neutral"] > 0:
        return "neutral", text
    match = re.search(
        r"\b(happy|joy|excited|smile|sad|angry|fear|disgust|frustrated|neutral|positive|negative)\b",
        text,
        re.I,
    )
    if not match:
        return "neutral", text
    return _normalize_emotion_detail(match.group(1)), text


def _extract_counts_from_text(text: str) -> dict[str, int]:
    cleaned = text.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    if start == -1:
        return {}
    depth = 0
    end = -1
    for idx, ch in enumerate(cleaned[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = idx
                break
    if end == -1 or end <= start:
        return {}
    try:
        payload = json.loads(cleaned[start : end + 1])
    except Exception:
        return {}
    counts = payload.get("emotion_counts")
    if not isinstance(counts, dict):
        return {}
    normalized: dict[str, int] = {}
    for k, v in counts.items():
        emotion = _normalize_emotion_detail(str(k))
        try:
            n = int(v)
        except Exception:
            continue
        if n > 0:
            normalized[emotion] = normalized.get(emotion, 0) + n
    return normalized


def _has_nonzero_counts(counts: dict[str, int] | None) -> bool:
    if not counts:
        return False
    return any(v > 0 for v in counts.values())


def _dominant_from_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "neutral"
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[0][0]


async def analyze_face_sentiment(
    frame_bytes: bytes,
) -> tuple[str, str, str | None, str | None, dict[str, int] | None]:
    if not _emotion_config.endpoint:
        # Stub mode: neutral by default.
        return "neutral", "stub", None, None, None

    headers = {"Authorization": f"Bearer {_emotion_config.token}"} if _emotion_config.token else {}
    # Temporary compatibility for private endpoints with non-public CA chains.
    verify_tls = not _emotion_config.endpoint.endswith(".pcaidev.ai.greendatacenter.com/v1/chat/completions")
    try:
        async with httpx.AsyncClient(timeout=10, verify=verify_tls) as client:
            if "/v1/chat/completions" in _emotion_config.endpoint:
                image_b64 = base64.b64encode(frame_bytes).decode("ascii")
                req_headers = {**headers, "Content-Type": "application/json"}
                payload = {
                    "model": _emotion_config.model,
                    "temperature": 0.2,
                    "max_tokens": 220,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Analyze all visible human faces in the image. "
                                "Return strict JSON only with this schema: "
                                "{\"emotion_counts\":{\"neutral\":0,\"happy\":0,\"joy\":0,\"excited\":0,\"smile\":0,"
                                "\"sad\":0,\"angry\":0,\"fear\":0,\"disgust\":0,\"frustrated\":0},"
                                "\"dominant_emotion\":\"neutral\"}. "
                                "Use only these emotion labels as keys. "
                                "Counts must be non-negative integers. "
                                "dominant_emotion must be one of those labels. "
                                "If at least one face is visible, the sum of emotion_counts must be >= 1. "
                                "Do not return all-zero counts when a face is visible. "
                                "Do not wrap JSON in markdown, code fences, or prose."
                            ),
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Count face emotions in this image and provide JSON only."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                            ],
                        },
                    ],
                }
                resp = await client.post(_emotion_config.endpoint, headers=req_headers, json=payload)
                if resp.status_code >= 400:
                    return "neutral", "fallback", f"HTTP {resp.status_code}: {resp.text[:500]}", None, None
                data = resp.json()
                detail, raw_text = _extract_emotion_detail_from_chat(data)
                counts = _extract_counts_from_text(raw_text)
                if counts:
                    detail = _dominant_from_counts(counts)
                detail = _stabilize_emotion(detail)
                return detail, "nim-chat", None, raw_text, counts if counts else None

            files = {"frame": ("frame.jpg", frame_bytes, "image/jpeg")}
            data = {"model": _emotion_config.model} if _emotion_config.model else None
            resp = await client.post(_emotion_config.endpoint, headers=headers, files=files, data=data)
            if resp.status_code >= 400:
                return "neutral", "fallback", f"HTTP {resp.status_code}: {resp.text[:500]}", None, None
            data = resp.json()
            sentiment = data.get("sentiment") or data.get("emotion") or "neutral"
            detail = _normalize_emotion_detail(str(sentiment))
            detail = _stabilize_emotion(detail)
            return detail, "external", None, str(sentiment), None
    except Exception as exc:
        return "neutral", "fallback", str(exc), None, None


@app.post("/vision")
async def vision(frame: UploadFile = File(...)):
    data = await frame.read()
    face_count = 0
    emotion_counts: dict[str, int] = {}
    sentiment_source = "nim-chat"
    sentiment_error = None
    emotion_raw = None
    detected_faces = 0
    analyzed_faces = 0
    counts_source = "none"

    np_img = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if img is not None and not _face_cascade.empty():
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = _face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(48, 48),
        )
        face_count = len(faces)
        detected_faces = face_count

        if face_count > 0:
            # Limit per-frame model calls for latency and cost.
            cropped_blobs: list[bytes] = []
            for (x, y, w, h) in faces[:4]:
                face_crop = img[y : y + h, x : x + w]
                ok, enc = cv2.imencode(".jpg", face_crop)
                if ok:
                    cropped_blobs.append(enc.tobytes())
            analyzed_faces = len(cropped_blobs)

            results = []
            for crop_bytes in cropped_blobs:
                results.append(await analyze_face_sentiment(crop_bytes))

            raw_chunks = []
            for detail, source, err, raw, counts in results:
                sentiment_source = source
                if err and not sentiment_error:
                    sentiment_error = err
                if raw:
                    raw_chunks.append(raw)
                if _has_nonzero_counts(counts):
                    for k, v in counts.items():
                        emotion_counts[k] = emotion_counts.get(k, 0) + v
                    counts_source = "model-per-face"
                else:
                    emotion_counts[detail] = emotion_counts.get(detail, 0) + 1
                    if counts_source == "none":
                        counts_source = "fallback-per-face"

            if raw_chunks:
                emotion_raw = " | ".join(raw_chunks[:4])

    if face_count == 0:
        # Fallback to whole-frame classification when no face box is found.
        emotion_detail, sentiment_source, sentiment_error, emotion_raw, frame_counts = await analyze_face_sentiment(data)
        if _has_nonzero_counts(frame_counts):
            emotion_counts = frame_counts or {}
            face_count = max(1, sum(emotion_counts.values()))
            counts_source = "model-full-frame"
        else:
            face_count = max(1, face_count)
            emotion_counts = {emotion_detail: face_count}
            counts_source = "fallback-full-frame"

    dominant_detail = _dominant_from_counts(emotion_counts) if emotion_counts else "neutral"
    return {
        "face_count": face_count,
        "bytes": len(data),
        "sentiment": _emotion_bucket(dominant_detail),
        "emotion_detail": dominant_detail,
        "emotion_counts": emotion_counts,
        "emotion_raw": emotion_raw,
        "sentiment_source": sentiment_source,
        "sentiment_error": sentiment_error,
        "debug": {
            "detected_faces": detected_faces,
            "analyzed_faces": analyzed_faces,
            "counts_source": counts_source,
        },
    }


class SentimentRequest(BaseModel):
    text: str


def analyze_sentiment(text: str) -> str:
    # Simple heuristic for demo use; replace with real model as needed.
    positive = {"good", "great", "excellent", "love", "happy", "awesome", "fantastic", "positive"}
    negative = {"bad", "terrible", "awful", "hate", "sad", "angry", "negative", "horrible"}
    tokens = {t.strip(".,!?;:").lower() for t in text.split()}
    score = len(tokens & positive) - len(tokens & negative)
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


@app.post("/sentiment")
async def sentiment(payload: SentimentRequest):
    label = analyze_sentiment(payload.text)
    return {"sentiment": label}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/emotion-config")
async def get_emotion_config():
    return _emotion_config


@app.post("/emotion-config")
async def set_emotion_config(payload: EmotionConfig):
    _emotion_config.endpoint = payload.endpoint.strip()
    _emotion_config.token = payload.token.strip()
    _emotion_config.model = payload.model.strip()
    _save_emotion_config(_emotion_config)
    return _emotion_config
