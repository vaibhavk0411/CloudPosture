import { useEffect, useState } from "react";
import { History, TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  cloudApi,
  type ScanRecord,
  type TrendResponse,
} from "../services/api";
import TrendChart from "../components/charts/TrendChart";
import DataTable, { type Column } from "../components/tables/DataTable";

export default function ScanHistory() {
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [trend, setTrend] = useState<TrendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [s, t] = await Promise.all([
          cloudApi.getScans(),
          cloudApi.getTrend(20).catch(() => null),
        ]);
        setScans(s.scans ?? []);
        if (t) setTrend(t);
      } catch (e: any) {
        setErr(e?.message ?? "Failed to load scan history");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const columns: Column<ScanRecord>[] = [
    {
      key: "scan_id",
      header: "Scan ID",
      sortable: true,
      render: (r) => (
        <span className="font-mono text-xs text-brand-300">{r.scan_id}</span>
      ),
    },
    {
      key: "timestamp",
      header: "Timestamp",
      sortable: true,
      sortValue: (r) => new Date(r.timestamp).getTime(),
      render: (r) => (
        <span className="text-sm text-slate-300">
          {new Date(r.timestamp).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}
        </span>
      ),
    },
    {
      key: "summary.compliance_score" as any,
      header: "Score",
      sortable: true,
      sortValue: (r) => r.summary.compliance_score,
      render: (r) => {
        const s = r.summary.compliance_score;
        const color =
          s >= 90 ? "text-emerald-300" : s >= 70 ? "text-amber-300" : "text-red-300";
        return <span className={`font-bold ${color}`}>{s.toFixed(1)}%</span>;
      },
    },
    {
      key: "summary.passed" as any,
      header: "Passed",
      render: (r) => (
        <span className="text-emerald-300 font-semibold">{r.summary.passed}</span>
      ),
    },
    {
      key: "summary.failed" as any,
      header: "Failed",
      render: (r) => (
        <span className="text-red-300 font-semibold">{r.summary.failed}</span>
      ),
    },
    {
      key: "summary.total_checks" as any,
      header: "Total",
      render: (r) => r.summary.total_checks,
    },
  ];

  const ImprovementBadge = () => {
    if (!trend) return null;
    const v = trend.improvement;
    const Icon = v > 0 ? TrendingUp : v < 0 ? TrendingDown : Minus;
    const color =
      v > 0
        ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30"
        : v < 0
        ? "text-red-300 bg-red-500/10 border-red-500/30"
        : "text-slate-300 bg-slate-500/10 border-slate-500/30";
    return (
      <span className={`badge ${color}`}>
        <Icon className="w-3.5 h-3.5" />
        {v >= 0 ? "+" : ""}
        {v.toFixed(1)}% across {trend.scans_in_trend} scans
      </span>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-brand-400" /> Scan History
          </h2>
          <p className="text-sm text-slate-400">
            {scans.length} scans persisted in DynamoDB
          </p>
        </div>
        <ImprovementBadge />
      </div>

      {err && (
        <div className="card p-4 border-red-500/30 bg-red-500/5 text-red-300 text-sm">
          {err}
        </div>
      )}

      {trend && trend.trend.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div>
              <h3 className="text-sm font-semibold text-white">
                Compliance Progression
              </h3>
              <p className="text-xs text-slate-400">
                Latest: {trend.latest_score.toFixed(1)}% • Oldest:{" "}
                {trend.oldest_score.toFixed(1)}% • Average:{" "}
                {trend.average_score.toFixed(1)}%
              </p>
            </div>
          </div>
          <TrendChart data={trend.trend} />
        </div>
      )}

      <DataTable
        columns={columns}
        data={scans}
        loading={loading}
        searchKeys={["scan_id"]}
        emptyText="No scans yet — click 'Run New Scan' in the top bar."
      />
    </div>
  );
}
