import { Loader2, RefreshCw } from "lucide-react";
import { useState } from "react";
import { cloudApi } from "../../services/api";
import toast from "react-hot-toast";

interface Props {
  onScanComplete?: () => void;
}

export default function Topbar({ onScanComplete }: Props) {
  const [running, setRunning] = useState(false);

  const handleScan = async () => {
    setRunning(true);
    const t = toast.loading("Running new posture scan...");
    try {
      const result = await cloudApi.runScan();
      toast.success(
        `Scan complete: ${result.summary.compliance_score.toFixed(1)}% compliance`,
        { id: t }
      );
      onScanComplete?.();
    } catch (e: any) {
      toast.error(
        e?.response?.data?.detail ?? "Scan failed. Check backend logs.",
        { id: t }
      );
    } finally {
      setRunning(false);
    }
  };

  return (
    <header className="h-16 border-b border-white/5 bg-ink-900/40 backdrop-blur sticky top-0 z-20">
      <div className="h-full px-4 md:px-8 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-base md:text-lg font-semibold text-white">
            Cloud Security Posture
          </h1>
          <span className="badge bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden md:inline text-xs text-slate-400">
            AWS Account • CIS v1.5
          </span>
          <button
            onClick={handleScan}
            disabled={running}
            className="btn-primary"
          >
            {running ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            {running ? "Scanning..." : "Run New Scan"}
          </button>
        </div>
      </div>
    </header>
  );
}
