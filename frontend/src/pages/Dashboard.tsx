import { useEffect, useState } from "react";
import {
  Activity,
  Server,
  Database,
  ShieldCheck,
  ShieldX,
  ListChecks,
  Clock,
  TrendingUp,
} from "lucide-react";
import StatCard from "../components/dashboard/StatCard";
import ScoreRing from "../components/dashboard/ScoreRing";
import TrendChart from "../components/charts/TrendChart";
import StatusPie from "../components/charts/StatusPie";
import {
  cloudApi,
  type CISResults,
  type EC2Instance,
  type S3Bucket,
  type TrendResponse,
} from "../services/api";
import Skeleton from "../components/ui/Skeleton";

export default function Dashboard() {
  const [cis, setCis] = useState<CISResults | null>(null);
  const [instances, setInstances] = useState<EC2Instance[]>([]);
  const [buckets, setBuckets] = useState<S3Bucket[]>([]);
  const [trend, setTrend] = useState<TrendResponse | null>(null);
  const [lastScan, setLastScan] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        // Parallel fetch — performance matters in a demo
        const [cisRes, ec2Res, s3Res] = await Promise.all([
          cloudApi.getCisResults(),
          cloudApi.getInstances(),
          cloudApi.getBuckets(),
        ]);
        if (!alive) return;
        setCis(cisRes);
        setInstances(ec2Res.instances ?? []);
        setBuckets(s3Res.buckets ?? []);

        // Optional - may 404 if no scans persisted yet
        try {
          const trendRes = await cloudApi.getTrend(10);
          if (alive) setTrend(trendRes);
        } catch { /* trend optional */ }
        try {
          const summary = await cloudApi.getSummary();
          if (alive) setLastScan(summary.timestamp);
        } catch { /* summary optional */ }
      } catch (e: any) {
        if (alive) setError(e?.message ?? "Failed to load dashboard");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const score = cis?.summary.compliance_score ?? 0;
  const summary = cis?.summary;

  const verdict =
    score >= 90
      ? { label: "Excellent", color: "text-emerald-300" }
      : score >= 70
      ? { label: "Acceptable", color: "text-amber-300" }
      : { label: "Needs Attention", color: "text-red-300" };

  return (
    <div className="space-y-6">
      {/* Hero header */}
      <div className="card p-6 md:p-8 bg-gradient-to-br from-ink-900 via-ink-800 to-ink-900 relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-72 h-72 bg-brand-500/20 rounded-full blur-3xl" />
        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div className="md:col-span-2">
            <p className="text-xs uppercase tracking-widest text-brand-400 font-bold">
              Executive Summary
            </p>
            <h2 className="text-2xl md:text-3xl font-bold mt-2">
              Your Cloud Security Posture is{" "}
              <span className={verdict.color}>{verdict.label}</span>
            </h2>
            <p className="text-slate-400 mt-2 text-sm max-w-xl">
              Continuous CIS AWS Foundations Benchmark assessment across EC2,
              S3, IAM, CloudTrail and Security Groups.
            </p>
            {lastScan && (
              <p className="text-xs text-slate-500 mt-4 flex items-center gap-2">
                <Clock className="w-3.5 h-3.5" />
                Last scan: {new Date(lastScan).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}
              </p>
            )}
          </div>
          <div className="flex justify-center md:justify-end">
            {loading ? (
              <div className="w-40 h-40 rounded-full bg-white/5 animate-pulse" />
            ) : (
              <ScoreRing score={score} />
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="card p-4 border-red-500/30 bg-red-500/5 text-red-300 text-sm">
          {error} — make sure the backend is running on{" "}
          <code className="bg-black/30 px-1 rounded">localhost:8000</code>.
        </div>
      )}

      {/* KPI grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Checks"
          value={summary?.total_checks ?? "—"}
          icon={ListChecks}
          accent="brand"
          loading={loading}
        />
        <StatCard
          title="Passed"
          value={summary?.passed ?? "—"}
          icon={ShieldCheck}
          accent="emerald"
          loading={loading}
        />
        <StatCard
          title="Failed"
          value={summary?.failed ?? "—"}
          icon={ShieldX}
          accent="red"
          loading={loading}
        />
        <StatCard
          title="Errors"
          value={summary?.errors ?? "—"}
          icon={Activity}
          accent="amber"
          loading={loading}
        />
        <StatCard
          title="EC2 Instances"
          value={instances.length}
          subtitle={`${
            new Set(instances.map((i) => i.region)).size
          } regions`}
          icon={Server}
          accent="violet"
          loading={loading}
        />
        <StatCard
          title="S3 Buckets"
          value={buckets.length}
          subtitle={`${
            buckets.filter((b) => b.access_level === "Public").length
          } public`}
          icon={Database}
          accent="brand"
          loading={loading}
        />
        <StatCard
          title="Avg Score (10 scans)"
          value={trend ? `${trend.average_score.toFixed(1)}%` : "—"}
          icon={TrendingUp}
          accent="emerald"
          loading={loading}
        />
        <StatCard
          title="Improvement"
          value={
            trend
              ? `${trend.improvement >= 0 ? "+" : ""}${trend.improvement.toFixed(
                  1
                )}%`
              : "—"
          }
          subtitle={trend ? `Across ${trend.scans_in_trend} scans` : undefined}
          icon={TrendingUp}
          accent={trend && trend.improvement >= 0 ? "emerald" : "red"}
          loading={loading}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">
                Compliance Trend
              </h3>
              <p className="text-xs text-slate-400">
                Historical compliance score across scans
              </p>
            </div>
            {trend && (
              <span className="badge bg-brand-500/15 text-brand-300 border border-brand-500/30">
                {trend.scans_in_trend} scans
              </span>
            )}
          </div>
          {loading ? (
            <Skeleton rows={6} />
          ) : trend && trend.trend.length > 0 ? (
            <TrendChart data={trend.trend} />
          ) : (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-sm gap-2">
              <TrendingUp className="w-8 h-8 opacity-40" />
              <p>No historical scans yet.</p>
              <p className="text-xs">
                Click "Run New Scan" to start tracking trends.
              </p>
            </div>
          )}
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white">Check Breakdown</h3>
          <p className="text-xs text-slate-400 mb-2">
            PASS / FAIL / ERROR distribution
          </p>
          {loading || !summary ? (
            <Skeleton rows={5} />
          ) : (
            <StatusPie summary={summary} />
          )}
        </div>
      </div>
    </div>
  );
}
