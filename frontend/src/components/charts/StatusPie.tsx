import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import type { CISSummary } from "../../services/api";

interface Props {
  summary: CISSummary;
}

const COLORS = {
  Passed: "#34d399",
  Failed: "#f87171",
  Errors: "#fbbf24",
};

export default function StatusPie({ summary }: Props) {
  const data = [
    { name: "Passed", value: summary.passed },
    { name: "Failed", value: summary.failed },
    { name: "Errors", value: summary.errors },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="h-[240px] flex items-center justify-center text-slate-500 text-sm">
        No data
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={3}
          stroke="none"
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={COLORS[entry.name as keyof typeof COLORS]}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Legend
          verticalAlign="bottom"
          iconType="circle"
          wrapperStyle={{ fontSize: 12, color: "#94a3b8" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
