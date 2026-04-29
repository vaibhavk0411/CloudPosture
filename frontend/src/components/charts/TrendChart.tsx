import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import type { TrendPoint } from "../../services/api";

interface Props {
  data: TrendPoint[];
}

export default function TrendChart({ data }: Props) {
  const chartData = data.map((d) => ({
    name: new Date(d.timestamp).toLocaleDateString("en-IN", {
      timeZone: "Asia/Kolkata",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }),
    score: Number(d.compliance_score?.toFixed?.(2) ?? d.compliance_score),
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={chartData} margin={{ left: -10, right: 10, top: 10, bottom: 0 }}>
        <defs>
          <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4060ff" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#4060ff" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="name"
          stroke="#64748b"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#64748b"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          domain={[0, 100]}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: "#94a3b8" }}
          formatter={(v) => [`${v}%`, "Score"]}
        />
        <Area
          type="monotone"
          dataKey="score"
          stroke="#4060ff"
          strokeWidth={2}
          fill="url(#scoreFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
