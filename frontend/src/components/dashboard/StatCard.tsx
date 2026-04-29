import { type LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  accent?: "brand" | "emerald" | "red" | "amber" | "violet";
  loading?: boolean;
}

const accents = {
  brand: "text-brand-400 bg-brand-500/10 border-brand-500/30",
  emerald: "text-emerald-300 bg-emerald-500/10 border-emerald-500/30",
  red: "text-red-300 bg-red-500/10 border-red-500/30",
  amber: "text-amber-300 bg-amber-500/10 border-amber-500/30",
  violet: "text-violet-300 bg-violet-500/10 border-violet-500/30",
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accent = "brand",
  loading,
}: Props) {
  return (
    <div className="card card-hover p-5 flex items-start justify-between">
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
          {title}
        </p>
        <p className="text-3xl font-bold text-white mt-2">
          {loading ? <span className="inline-block h-7 w-20 rounded bg-white/5 animate-pulse" /> : value}
        </p>
        {subtitle && (
          <p className="text-xs text-slate-400 mt-1 truncate">{subtitle}</p>
        )}
      </div>
      <div className={`p-2.5 rounded-xl border ${accents[accent]}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}
