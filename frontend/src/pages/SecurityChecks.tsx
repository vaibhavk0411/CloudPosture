import { useEffect, useMemo, useState } from "react";
import { ShieldCheck, PartyPopper, AlertTriangle, ChevronDown, ChevronUp, Wrench } from "lucide-react";
import DataTable, { type Column } from "../components/tables/DataTable";
import StatusBadge from "../components/ui/StatusBadge";
import { cloudApi, type CISCheck, type CISResults, type CheckSeverity } from "../services/api";

type Filter = "ALL" | "PASS" | "FAIL" | "ERROR";

const severityConfig: Record<CheckSeverity, { label: string; className: string }> = {
  CRITICAL: { label: "Critical", className: "bg-red-500/15 text-red-300 border border-red-500/40" },
  HIGH:     { label: "High",     className: "bg-orange-500/15 text-orange-300 border border-orange-500/40" },
  MEDIUM:   { label: "Medium",   className: "bg-amber-500/15 text-amber-300 border border-amber-500/40" },
  LOW:      { label: "Low",      className: "bg-slate-500/15 text-slate-300 border border-slate-500/30" },
};

function SeverityBadge({ severity }: { severity?: CheckSeverity }) {
  if (!severity) return null;
  const cfg = severityConfig[severity] ?? severityConfig.MEDIUM;
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${cfg.className}`}>
      {severity === "CRITICAL" && <AlertTriangle className="w-2.5 h-2.5" />}
      {cfg.label}
    </span>
  );
}

function RemediationRow({ remediation }: { remediation?: string }) {
  const [open, setOpen] = useState(false);
  if (!remediation) return null;
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 text-[11px] text-brand-400 hover:text-brand-300 transition-colors"
      >
        <Wrench className="w-3 h-3" />
        Remediation
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <p className="mt-1.5 text-[11px] text-slate-400 leading-relaxed bg-white/[0.03] border border-white/5 rounded-lg p-3 font-mono whitespace-pre-wrap">
          {remediation}
        </p>
      )}
    </div>
  );
}

export default function SecurityChecks() {
  const [data, setData] = useState<CISResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("ALL");

  useEffect(() => {
    cloudApi
      .getCisResults()
      .then(setData)
      .catch((e) => setErr(e?.message ?? "Failed to load checks"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (filter === "ALL") return data.checks;
    return data.checks.filter((c) => c.status === filter);
  }, [data, filter]);

  const columns: Column<CISCheck>[] = [
    {
      key: "check_name",
      header: "Check",
      sortable: true,
      render: (r) => (
        <div className="min-w-0">
          <p className="font-medium text-white text-sm">{r.check_name}</p>
          {r.cis_id && (
            <p className="text-[11px] text-slate-500 mt-0.5 font-mono">{r.cis_id}</p>
          )}
        </div>
      ),
    },
    {
      key: "severity",
      header: "Severity",
      sortable: true,
      sortValue: (r) => {
        const order: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
        return order[r.severity ?? "MEDIUM"] ?? 2;
      },
      render: (r) => <SeverityBadge severity={r.severity} />,
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (r) => <StatusBadge status={r.status} />,
    },
    {
      key: "resource",
      header: "Resource",
      render: (r) => (
        <span className="font-mono text-xs text-slate-300">{r.resource}</span>
      ),
    },
    {
      key: "evidence",
      header: "Evidence / Remediation",
      render: (r) => (
        <div className="max-w-sm">
          <p className="text-xs text-slate-400 leading-relaxed">{r.evidence}</p>
          {r.status !== "PASS" && <RemediationRow remediation={r.remediation} />}
        </div>
      ),
    },
  ];

  const summary = data?.summary;
  const failed = summary?.failed ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-brand-400" /> CIS AWS Benchmark
          </h2>
          <p className="text-sm text-slate-400">
            Foundations v1.5 • {summary?.total_checks ?? 0} controls evaluated
          </p>
        </div>
        <div className="flex gap-2">
          {(["ALL", "PASS", "FAIL", "ERROR"] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                filter === f
                  ? "bg-brand-500/20 text-white border-brand-500/40"
                  : "bg-white/5 text-slate-400 border-white/10 hover:text-white"
              }`}
            >
              {f}
              {data && f !== "ALL" && (
                <span className="ml-1.5 text-slate-500">
                  {data.checks.filter((c) => c.status === f).length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {err && (
        <div className="card p-4 border-red-500/30 bg-red-500/5 text-red-300 text-sm">
          {err}
        </div>
      )}

      {!loading && summary && failed === 0 && (
        <div className="card p-6 bg-gradient-to-br from-emerald-500/10 to-brand-500/10 border-emerald-500/30 flex items-center gap-4">
          <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/40">
            <PartyPopper className="w-6 h-6 text-emerald-300" />
          </div>
          <div>
            <p className="text-lg font-bold text-white">100% Secure</p>
            <p className="text-sm text-slate-400">
              All {summary.total_checks} CIS controls passed. No failed checks
              detected.
            </p>
          </div>
        </div>
      )}

      <DataTable
        columns={columns}
        data={filtered}
        loading={loading}
        searchKeys={["check_name", "resource", "evidence", "cis_id"]}
        emptyText={
          filter === "FAIL"
            ? "No failed checks — your environment is secure!"
            : "No checks to display."
        }
      />
    </div>
  );
}
