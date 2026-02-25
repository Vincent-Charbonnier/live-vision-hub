import { Users } from "lucide-react";

interface DetectionResultsProps {
  faceCount: number | null;
  isActive: boolean;
  lastResponse: Record<string, unknown> | null;
  sentiment: string | null;
  error: string | null;
}

const DetectionResults = ({
  faceCount,
  isActive,
  lastResponse,
  sentiment,
  error,
}: DetectionResultsProps) => {
  if (error) {
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4">
        <p className="text-sm text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Face count card */}
      <div className="flex items-center gap-4 rounded-xl border-glow bg-card p-4">
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-lg ${
            faceCount && faceCount > 0
              ? "bg-primary/20 text-primary"
              : "bg-secondary text-muted-foreground"
          }`}
        >
          <Users className="h-6 w-6" />
        </div>
        <div className="flex-1">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Faces Detected
          </p>
          <p className="text-3xl font-bold tabular-nums text-foreground">
            {faceCount !== null ? faceCount : "—"}
          </p>
        </div>
        {isActive && (
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 animate-pulse-glow rounded-full bg-primary" />
            <span className="text-xs text-primary">LIVE</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between rounded-xl border-glow bg-card p-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Face Sentiment
          </p>
          <p className="text-2xl font-bold text-foreground">
            {sentiment ?? "—"}
          </p>
        </div>
      </div>

      {/* Raw response */}
      {lastResponse && (
        <details className="group">
          <summary className="cursor-pointer rounded-lg bg-secondary/50 px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground">
            Raw Response
          </summary>
          <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-muted p-3 text-xs text-muted-foreground">
            {JSON.stringify(lastResponse, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};

export default DetectionResults;
