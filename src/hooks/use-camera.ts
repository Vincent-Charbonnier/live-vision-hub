import { useRef, useState, useCallback, useEffect } from "react";

interface UseCameraOptions {
  onFrame?: (blob: Blob) => void;
  intervalMs?: number;
}

export function useCamera({ onFrame, intervalMs = 1000 }: UseCameraOptions = {}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsActive(true);
    } catch (err) {
      setError("Camera access denied. Please allow camera permissions.");
      console.error(err);
    }
  }, []);

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsActive(false);
  }, []);

  const captureFrame = useCallback((): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return Promise.resolve(null);
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")!.drawImage(video, 0, 0);
    return new Promise((resolve) => canvas.toBlob((b) => resolve(b), "image/jpeg", 0.8));
  }, []);

  useEffect(() => {
    if (!isActive || !onFrame) return;
    const run = async () => {
      const blob = await captureFrame();
      if (blob) onFrame(blob);
    };
    run();
    intervalRef.current = setInterval(run, intervalMs);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isActive, onFrame, intervalMs, captureFrame]);

  useEffect(() => {
    return () => stop();
  }, [stop]);

  return { videoRef, isActive, error, start, stop, captureFrame };
}
