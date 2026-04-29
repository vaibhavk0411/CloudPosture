import { useEffect, useState } from "react";
import { Database, Lock, Unlock, ShieldAlert } from "lucide-react";
import DataTable, { type Column } from "../components/tables/DataTable";
import { cloudApi, type S3Bucket } from "../services/api";

export default function S3Buckets() {
  const [data, setData] = useState<S3Bucket[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    cloudApi
      .getBuckets()
      .then((r) => setData(r.buckets ?? []))
      .catch((e) => setErr(e?.message ?? "Failed to load buckets"))
      .finally(() => setLoading(false));
  }, []);

  const columns: Column<S3Bucket>[] = [
    {
      key: "bucket_name",
      header: "Bucket Name",
      sortable: true,
      render: (r) => (
        <span className="font-medium text-white">{r.bucket_name}</span>
      ),
    },
    { key: "region", header: "Region", sortable: true },
    {
      key: "encryption_status",
      header: "Encryption",
      sortable: true,
      render: (r) => {
        const enabled =
          r.encryption_status?.toLowerCase().includes("enabled") ||
          r.encryption_status?.toLowerCase().includes("aes") ||
          r.encryption_status?.toLowerCase().includes("kms");
        return (
          <span
            className={`badge ${
              enabled
                ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                : "bg-red-500/15 text-red-300 border border-red-500/30"
            }`}
          >
            {enabled ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
            {r.encryption_status || "Unknown"}
          </span>
        );
      },
    },
    {
      key: "access_level",
      header: "Access",
      sortable: true,
      render: (r) => {
        const isPublic = r.access_level === "Public";
        return (
          <span
            className={`badge ${
              isPublic
                ? "bg-red-500/15 text-red-300 border border-red-500/30"
                : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
            }`}
          >
            {isPublic ? <ShieldAlert className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
            {r.access_level}
          </span>
        );
      },
    },
    {
      key: "versioning",
      header: "Versioning",
      render: (r) => (
        <span className="text-xs text-slate-400">{r.versioning ?? "—"}</span>
      ),
    },
  ];

  const publicCount = data.filter((b) => b.access_level === "Public").length;
  const unencryptedCount = data.filter(
    (b) => !b.encryption_status?.toLowerCase().includes("enabled") &&
           !b.encryption_status?.toLowerCase().includes("aes") &&
           !b.encryption_status?.toLowerCase().includes("kms")
  ).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-brand-400" /> S3 Buckets
          </h2>
          <p className="text-sm text-slate-400">
            {data.length} buckets • {publicCount} public • {unencryptedCount} unencrypted
          </p>
        </div>
        {publicCount > 0 && (
          <span className="badge bg-red-500/15 text-red-300 border border-red-500/30">
            <ShieldAlert className="w-3 h-3" />
            {publicCount} public bucket{publicCount > 1 ? "s" : ""} detected
          </span>
        )}
      </div>

      {err && (
        <div className="card p-4 border-red-500/30 bg-red-500/5 text-red-300 text-sm">
          {err}
        </div>
      )}

      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        searchKeys={["bucket_name", "region", "access_level", "encryption_status"]}
        emptyText="No S3 buckets found."
      />
    </div>
  );
}
