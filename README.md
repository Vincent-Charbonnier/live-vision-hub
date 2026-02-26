# Live Vision Hub (HPE Demo)

Live Vision Hub is a camera-based web app for live face presence and emotion analysis.
It includes a React frontend and a FastAPI backend, supports Docker, and ships with a Helm chart generator for Kubernetes/Istio deployment.

---

## Overview

The application provides:

- Browser camera capture with live scanning UI
- Backend frame processing on `POST /vision`
- Face count reporting
- Emotion classification with detailed labels (`happy`, `joy`, `excited`, `smile`, `sad`, `angry`, `fear`, `disgust`, `frustrated`, `neutral`)
- Aggregated emotion counts (example: `2 neutral, 1 happy`)
- Configurable emotion model endpoint, model name, and token via UI settings
- Persisted backend emotion config (`/data/emotion-config.json`)

---

## Architecture

  - Frontend (React/Vite) captures webcam frames in the browser and POSTs them to backend /vision.
  - Backend (FastAPI) runs CPU face detection with OpenCV Haar cascade (haarcascade_frontalface_default).
  - Backend crops detected face regions from each frame.
  - For each face crop, backend calls external VLM endpoint (NVIDIA NIM, OpenAI-compatible /v1/chat/completions) to
    infer emotion.
  - Backend aggregates per-face emotions into:
      - face_count
      - emotion_counts (e.g., 2 neutral, 1 happy)
      - emotion_detail (dominant label)
      - sentiment bucket (positive|neutral|negative)
  - Frontend displays live counts and raw backend response.

<img width="1022" height="428" alt="image" src="https://github.com/user-attachments/assets/537ad56e-b1fb-496e-8c30-4a1a0fbb5aee" />

Main backend endpoints:

- `POST /vision` -> frame upload and inference
- `GET /health` -> health check
- `GET /emotion-config` -> current model config
- `POST /emotion-config` -> update model config

Example `/vision` response:

```json
{
  "face_count": 3,
  "sentiment": "neutral",
  "emotion_detail": "happy",
  "emotion_counts": { "neutral": 2, "happy": 1 },
  "sentiment_source": "nim-chat",
  "sentiment_error": null
}
```

---

## Local Docker Run

### 1. Build images

```sh
docker build -t vinchar/live-vision-hub:0.0.1 .
docker build -t live-vision-backend:0.0.1 -f backend/Dockerfile backend
```

### 2. Run backend (with persisted config)

```sh
docker run -d --name live-vision-backend -p 8000:8000 --restart unless-stopped \
  -v ./backend/data:/data \
  live-vision-backend:0.0.1
```

### 3. Run frontend

```sh
docker run -d --name live-vision-hub -p 3000:80 --restart unless-stopped \
  vinchar/live-vision-hub:0.0.1
```

### 4. Open app

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

Use the settings icon in the app header to configure:

- Emotion endpoint (`.../v1/chat/completions`)
- Emotion model
- Emotion token

---

## Helm Chart Generation

Helm chart generator script:

- `generate_live_vision_helm_chart.py`

Generate chart + package:

```sh
python generate_live_vision_helm_chart.py
```

Outputs:

- Chart folder: `live-vision/`
- Packaged chart: `live-vision-0.0.1.tgz`

Install:

```sh
helm install live-vision live-vision-0.0.1.tgz
```

The generated chart includes:

- Frontend and backend deployments/services
- Istio `VirtualService` path routing (`/`, `/vision`, `/emotion-config`)
- Optional Ingress
- Configurable emotion endpoint/model/token secret in `values.yaml`
- Optional PVC for backend data persistence

---

## Repository Structure

| Path | Description |
|---|---|
| `src/` | React frontend |
| `backend/main.py` | FastAPI backend |
| `backend/Dockerfile` | Backend image |
| `backend/requirements.txt` | Backend Python deps |
| `Dockerfile` | Frontend image |
| `nginx.conf` | Frontend nginx config |
| `generate_live_vision_helm_chart.py` | Helm chart generator |
| `live-vision/` | Generated Helm chart directory |
| `live-vision-0.0.1.tgz` | Packaged Helm chart |

---
## Try yourself

<img width="447" height="442" alt="image" src="https://github.com/user-attachments/assets/cca76deb-440b-4b35-987a-5ed9b67ff098" />

---

## Troubleshooting

### Emotion stays neutral

- Check `Raw Response` in UI:
  - `sentiment_source`
  - `sentiment_error`
  - `emotion_raw`
- Confirm endpoint points to a vision-capable model API and token is valid.

### TLS/cert issues to private endpoint

- If using private cert chains, ensure backend trust configuration matches your environment.

### No camera input

- Allow browser camera permissions.
- Verify no other app is locking camera.
