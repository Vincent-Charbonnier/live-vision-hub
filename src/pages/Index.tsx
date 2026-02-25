import { useState, useCallback } from "react";
import { useCamera } from "@/hooks/use-camera";
import { sendFrameToBackend } from "@/lib/vision-api";
import CameraView from "@/components/CameraView";
import CameraControls from "@/components/CameraControls";
import DetectionResults from "@/components/DetectionResults";
import BackendConfig from "@/components/BackendConfig";
import { Scan } from "lucide-react";

const Index = () => {
  const [faceCount, setFaceCount] = useState<number | null>(null);
  const [lastResponse, setLastResponse] = useState<Record<string, unknown> | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [frameCount, setFrameCount] = useState(0);

  const handleFrame = useCallback(async (blob: Blob) => {
    setIsScanning(true);
    try {
      const data = await sendFrameToBackend(blob);
      setFaceCount(data.face_count);
      setLastResponse(data as Record<string, unknown>);
      setApiError(null);
      setFrameCount((c) => c + 1);
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Connection failed");
    }
  }, []);

  const { videoRef, isActive, error: cameraError, start, stop } = useCamera({
    onFrame: handleFrame,
    intervalMs: 1000,
  });

  const handleStop = () => {
    stop();
    setIsScanning(false);
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
            <BackendConfig />
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
                Sending 1 frame/sec
              </p>
            )}
          </div>

          <DetectionResults
            faceCount={faceCount}
            isActive={isActive}
            lastResponse={lastResponse}
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
