import { RefObject } from "react";
import { ScanLine } from "lucide-react";

interface CameraViewProps {
  videoRef: RefObject<HTMLVideoElement>;
  isActive: boolean;
  isScanning: boolean;
}

const CameraView = ({ videoRef, isActive, isScanning }: CameraViewProps) => {
  return (
    <div className="relative overflow-hidden rounded-xl border-glow bg-card">
      {!isActive && (
        <div className="flex aspect-video items-center justify-center">
          <div className="text-center">
            <ScanLine className="mx-auto mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Tap "Start Scan" to activate camera
            </p>
          </div>
        </div>
      )}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`w-full ${isActive ? "block" : "hidden"}`}
      />
      {isActive && isScanning && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute inset-x-0 h-1/3 animate-scan scan-overlay" />
          <div className="absolute inset-0 rounded-xl border border-primary/20" />
          {/* Corner markers */}
          <div className="absolute left-3 top-3 h-6 w-6 border-l-2 border-t-2 border-primary" />
          <div className="absolute right-3 top-3 h-6 w-6 border-r-2 border-t-2 border-primary" />
          <div className="absolute bottom-3 left-3 h-6 w-6 border-b-2 border-l-2 border-primary" />
          <div className="absolute bottom-3 right-3 h-6 w-6 border-b-2 border-r-2 border-primary" />
        </div>
      )}
    </div>
  );
};

export default CameraView;
