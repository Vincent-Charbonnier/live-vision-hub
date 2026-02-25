interface VisionResponse {
  face_count: number;
  [key: string]: unknown;
}

const DEFAULT_BACKEND = "http://localhost:8000";

export function getBackendUrl(): string {
  return DEFAULT_BACKEND;
}

export function setBackendUrl(url: string) {
  void url;
}

export async function sendFrameToBackend(blob: Blob): Promise<VisionResponse> {
  const backendUrl = getBackendUrl();
  const formData = new FormData();
  formData.append("frame", blob);

  const endpoint = backendUrl ? `${backendUrl}/vision` : "/vision";
  const res = await fetch(endpoint, { method: "POST", body: formData });

  if (!res.ok) throw new Error(`Backend error: ${res.status}`);
  return res.json();
}

export async function sendSentimentToBackend(text: string): Promise<{ sentiment: string }> {
  const backendUrl = getBackendUrl();
  const endpoint = backendUrl ? `${backendUrl}/sentiment` : "/sentiment";
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) throw new Error(`Backend error: ${res.status}`);
  return res.json();
}
