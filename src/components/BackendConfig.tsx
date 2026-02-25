import { useState, useEffect } from "react";
import { Settings, X } from "lucide-react";
import { getBackendUrl, setBackendUrl } from "@/lib/vision-api";

const BackendConfig = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [url, setUrl] = useState("");

  useEffect(() => {
    setUrl(getBackendUrl());
  }, []);

  const handleSave = () => {
    setBackendUrl(url.replace(/\/+$/, ""));
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="rounded-lg bg-secondary p-2 text-muted-foreground transition-colors hover:text-foreground"
        aria-label="Backend settings"
      >
        <Settings className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border-glow bg-card p-4 shadow-xl">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">Backend URL</h3>
            <button onClick={() => setIsOpen(false)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="http://192.168.1.100:8000"
            className="mb-3 w-full rounded-lg border border-border bg-muted px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <p className="mb-3 text-xs text-muted-foreground">
            Point to your FastAPI backend. Leave empty for same-origin.
          </p>
          <button
            onClick={handleSave}
            className="w-full rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90"
          >
            Save
          </button>
        </div>
      )}
    </div>
  );
};

export default BackendConfig;
