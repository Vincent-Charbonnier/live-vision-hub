interface VisionResponse {
  face_count: number;
  [key: string]: unknown;
}

const DEFAULT_BACKEND = "";

export function getBackendUrl(): string {
  return localStorage.getItem("vision-backend-url") || DEFAULT_BACKEND;
}

export function setBackendUrl(url: string) {
  localStorage.setItem("vision-backend-url", url);
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
