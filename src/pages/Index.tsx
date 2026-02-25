import { useState, useCallback, useEffect } from "react";
import { useCamera } from "@/hooks/use-camera";
import { getBackendUrl, sendFrameToBackend } from "@/lib/vision-api";
import CameraView from "@/components/CameraView";
import CameraControls from "@/components/CameraControls";
import DetectionResults from "@/components/DetectionResults";
import { Scan, Settings, X } from "lucide-react";

const Index = () => {
  const [faceCount, setFaceCount] = useState<number | null>(null);
  const [lastResponse, setLastResponse] = useState<Record<string, unknown> | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [sentimentResult, setSentimentResult] = useState<string | null>(null);
  const [emotionCounts, setEmotionCounts] = useState<Record<string, number>>({});
  const [emotionEndpoint, setEmotionEndpoint] = useState("");
  const [emotionToken, setEmotionToken] = useState("");
  const [emotionModel, setEmotionModel] = useState("");
  const [emotionConfigStatus, setEmotionConfigStatus] = useState<string | null>(null);
  const [isEmotionConfigOpen, setIsEmotionConfigOpen] = useState(false);

  const handleFrame = useCallback(async (blob: Blob) => {
    setIsScanning(true);
    try {
      const data = await sendFrameToBackend(blob);
      setFaceCount(data.face_count);
      setSentimentResult(
        typeof data.emotion_detail === "string"
          ? data.emotion_detail
          : (typeof data.sentiment === "string" ? data.sentiment : null),
      );
      if (data.emotion_counts && typeof data.emotion_counts === "object") {
        setEmotionCounts(data.emotion_counts as Record<string, number>);
      } else {
        setEmotionCounts({});
      }
      setLastResponse(data as Record<string, unknown>);
      setApiError(null);
      setFrameCount((c) => c + 1);
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Connection failed");
    }
  }, []);

  const { videoRef, isActive, error: cameraError, start, stop } = useCamera({
    onFrame: handleFrame,
    intervalMs: 350,
  });

  const handleStop = () => {
    stop();
    setIsScanning(false);
    setEmotionCounts({});
  };

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const base = getBackendUrl();
        const url = base ? `${base}/emotion-config` : "/emotion-config";
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        setEmotionEndpoint(data.endpoint || "");
        setEmotionToken(data.token || "");
        setEmotionModel(data.model || "");
      } catch {
        // ignore on load
      }
    };
    loadConfig();
  }, []);

  const saveEmotionConfig = async () => {
    setEmotionConfigStatus(null);
    try {
      const base = getBackendUrl();
      const url = base ? `${base}/emotion-config` : "/emotion-config";
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: emotionEndpoint,
          token: emotionToken,
          model: emotionModel,
        }),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      setEmotionConfigStatus("Saved");
    } catch (err) {
      setEmotionConfigStatus(err instanceof Error ? err.message : "Save failed");
    }
  };

  return (
    <div className="flex min-h-[100dvh] flex-col bg-background">
      {/* Header */}
      <header className="border-b border-border px-4 py-3">
        <div className="mx-auto flex max-w-2xl items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Scan className="h-4 w-4 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-sm font-bold leading-tight text-foreground">
                Live Vision
              </h1>
              <p className="text-[10px] font-medium uppercase tracking-widest text-primary">
                HPE Demo
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isActive && (
              <span className="rounded-md bg-secondary px-2 py-0.5 text-[10px] tabular-nums text-muted-foreground">
                {frameCount} frames
              </span>
            )}
            <div className="relative">
              <button
                onClick={() => setIsEmotionConfigOpen((v) => !v)}
                className="rounded-lg bg-secondary p-2 text-muted-foreground transition-colors hover:text-foreground"
                aria-label="Emotion model settings"
              >
                <Settings className="h-4 w-4" />
              </button>

              {isEmotionConfigOpen && (
                <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border-glow bg-card p-4 shadow-xl">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-foreground">Emotion Model Config</h3>
                    <button
                      onClick={() => setIsEmotionConfigOpen(false)}
                      className="text-muted-foreground hover:text-foreground"
                      aria-label="Close"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="grid gap-2">
                    <input
                      type="url"
                      value={emotionEndpoint}
                      onChange={(e) => setEmotionEndpoint(e.target.value)}
                      placeholder="Emotion endpoint URL"
                      className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                    />
                    <input
                      type="text"
                      value={emotionModel}
                      onChange={(e) => setEmotionModel(e.target.value)}
                      placeholder="Model name (e.g. nvidia/nemotron-nano-12b-v2)"
                      className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                    />
                    <input
                      type="password"
                      value={emotionToken}
                      onChange={(e) => setEmotionToken(e.target.value)}
                      placeholder="Bearer token (optional)"
                      className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                    />
                    <button
                      onClick={saveEmotionConfig}
                      className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90"
                    >
                      Save
                    </button>
                    {emotionConfigStatus && (
                      <p className="text-xs text-muted-foreground">{emotionConfigStatus}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 px-4 py-4">
        <div className="mx-auto max-w-2xl space-y-4">
          <CameraView videoRef={videoRef} isActive={isActive} isScanning={isScanning} />

          <div className="flex items-center justify-between">
            <CameraControls isActive={isActive} onStart={start} onStop={handleStop} />
            {isActive && (
              <p className="text-xs text-muted-foreground">
                Sending ~3 frames/sec
              </p>
            )}
          </div>

          <DetectionResults
            faceCount={faceCount}
            isActive={isActive}
            lastResponse={lastResponse}
            sentiment={sentimentResult}
            emotionCounts={emotionCounts}
            error={cameraError || apiError}
          />

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border px-4 py-3">
        <p className="text-center text-[10px] text-muted-foreground">
          Hewlett Packard Enterprise — Live Presence Scanner Demo
        </p>
      </footer>
    </div>
  );
};

export default Index;
