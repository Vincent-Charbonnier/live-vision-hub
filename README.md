# Live Vision Hub (HPE Demo)

Live Vision Hub is a lightweight web UI that captures camera frames in the browser and sends them to a backend for real-time face detection.  
It is designed as a demo-friendly frontend that can run locally or be containerized with Docker.

---

## Overview

The application provides:

- Browser-based camera capture
- 1 frame/sec streaming to a backend `/vision` endpoint
- Live face count display
- Raw response viewer for debugging
- Backend URL configuration from the UI

---

## Architecture

- Frontend: React + Vite + Tailwind
- Backend: External `/vision` endpoint (FastAPI or equivalent) returning JSON

Expected response shape:

```json
{ "face_count": 2, "any_other_fields": "..." }
```

---

## Configuration

The backend URL can be configured from the UI via the settings icon.  
If left blank, the app uses same-origin requests (`/vision`).

---

## Docker Usage

Build and run the frontend container:

```sh
docker build -t live-vision-hub .
docker run -d --name live-vision-hub -p 3000:80 --restart unless-stopped live-vision-hub
```

Then point the backend URL in the UI to your vision service (for example `http://localhost:8000`).

---

## Repository Structure

| File/Folder | Description |
|---|---|
| `Dockerfile` | Frontend build + nginx runtime image |
| `nginx.conf` | SPA routing for the static build |
| `src/` | React frontend source |
| `src/lib/vision-api.ts` | Backend request logic |
| `src/hooks/use-camera.ts` | Camera capture + frame scheduling |

---

## Troubleshooting

### Backend errors

- Ensure your backend exposes `POST /vision` and accepts `multipart/form-data` with a `frame` field.
- Check CORS settings if the backend is on a different host/port.

### Camera access denied

- Allow camera permissions in your browser.
- Verify the app is served over HTTPS if required by the browser.
