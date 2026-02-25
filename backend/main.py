import os
import httpx
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


async def analyze_face_sentiment(frame_bytes: bytes) -> tuple[str, str]:
    endpoint = os.getenv("EMOTION_ENDPOINT", "").strip()
    token = os.getenv("EMOTION_TOKEN", "").strip()

    if not endpoint:
        # Stub mode: neutral by default.
        return "neutral", "stub"

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            files = {"frame": ("frame.jpg", frame_bytes, "image/jpeg")}
            resp = await client.post(endpoint, headers=headers, files=files)
            resp.raise_for_status()
            data = resp.json()
            sentiment = data.get("sentiment") or data.get("emotion") or "neutral"
            return str(sentiment), "external"
    except Exception:
        return "neutral", "fallback"


@app.post("/vision")
async def vision(frame: UploadFile = File(...)):
    # Minimal stub: read bytes to ensure upload works.
    data = await frame.read()
    face_count = 1 if len(data) > 0 else 0
    sentiment, sentiment_source = await analyze_face_sentiment(data)
    return {
        "face_count": face_count,
        "bytes": len(data),
        "sentiment": sentiment,
        "sentiment_source": sentiment_source,
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
