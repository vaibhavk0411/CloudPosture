import { useEffect, useState } from "react";
import { Server } from "lucide-react";
import DataTable, { type Column } from "../components/tables/DataTable";
import { cloudApi, type EC2Instance } from "../services/api";

const stateColor = (s: string) => {
  switch (s.toLowerCase()) {
    case "running":
      return "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30";
    case "stopped":
      return "bg-slate-500/15 text-slate-300 border border-slate-500/30";
    case "terminated":
      return "bg-red-500/15 text-red-300 border border-red-500/30";
    default:
      return "bg-amber-500/15 text-amber-300 border border-amber-500/30";
  }
};

export default function EC2Resources() {
  const [data, setData] = useState<EC2Instance[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    cloudApi
      .getInstances()
      .then((r) => setData(r.instances ?? []))
      .catch((e) => setErr(e?.message ?? "Failed to load instances"))
      .finally(() => setLoading(false));
  }, []);

  const columns: Column<EC2Instance>[] = [
    {
      key: "instance_id",
      header: "Instance ID",
      sortable: true,
      render: (r) => (
        <span className="font-mono text-xs text-brand-300">{r.instance_id}</span>
      ),
    },
    { key: "instance_type", header: "Type", sortable: true },
    { key: "region", header: "Region", sortable: true },
    {
      key: "state",
      header: "State",
      sortable: true,
      render: (r) => (
        <span className={`badge ${stateColor(r.state)}`}>{r.state}</span>
      ),
    },
    {
      key: "public_ip",
      header: "Public IP",
      render: (r) =>
        r.public_ip && r.public_ip !== "N/A" ? (
          <span className="font-mono text-xs">{r.public_ip}</span>
        ) : (
          <span className="text-slate-500 text-xs">private</span>
        ),
    },
    {
      key: "security_groups",
      header: "Security Groups",
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          {(r.security_groups ?? []).slice(0, 3).map((sg, idx) => (
            <span
              key={idx}
              className="badge bg-white/5 text-slate-300 border border-white/10 font-mono text-xs"
              title={sg.group_id}
            >
              {sg.group_name}
            </span>
          ))}
          {(r.security_groups?.length ?? 0) > 3 && (
            <span className="text-xs text-slate-500">
              +{(r.security_groups?.length ?? 0) - 3}
            </span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Server className="w-5 h-5 text-brand-400" /> EC2 Resources
          </h2>
          <p className="text-sm text-slate-400">
            Live discovery across all AWS regions ({data.length} instances)
          </p>
        </div>
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
        searchKeys={["instance_id", "instance_type", "region", "state"]}
        emptyText="No EC2 instances discovered."
      />
    </div>
  );
}
