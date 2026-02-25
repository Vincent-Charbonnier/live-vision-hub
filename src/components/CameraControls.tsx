import { Camera, CameraOff } from "lucide-react";

interface CameraControlsProps {
  isActive: boolean;
  onStart: () => void;
  onStop: () => void;
}

const CameraControls = ({ isActive, onStart, onStop }: CameraControlsProps) => {
  return (
    <div className="flex items-center gap-3">
      {!isActive ? (
        <button
          onClick={onStart}
          className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90 glow-green-sm"
        >
          <Camera className="h-4 w-4" />
          Start Scan
        </button>
      ) : (
        <button
          onClick={onStop}
          className="flex items-center gap-2 rounded-lg bg-secondary px-5 py-2.5 text-sm font-semibold text-secondary-foreground transition-all hover:bg-destructive hover:text-destructive-foreground"
        >
          <CameraOff className="h-4 w-4" />
          Stop
        </button>
      )}
    </div>
  );
};

export default CameraControls;
