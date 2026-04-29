import { ShieldCheck, ShieldAlert, ShieldX, type LucideIcon } from "lucide-react";
import type { CheckStatus } from "../../services/api";

interface Props {
  status: CheckStatus | string;
}

const styles: Record<string, { cls: string; Icon: LucideIcon }> = {
  PASS: { cls: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30", Icon: ShieldCheck },
  FAIL: { cls: "bg-red-500/15 text-red-300 border border-red-500/30", Icon: ShieldX },
  ERROR: { cls: "bg-amber-500/15 text-amber-300 border border-amber-500/30", Icon: ShieldAlert },
};

export default function StatusBadge({ status }: Props) {
  const s = styles[status] ?? styles.ERROR;
  const Icon = s.Icon;
  return (
    <span className={`badge ${s.cls}`}>
      <Icon className="w-3.5 h-3.5" />
      {status}
    </span>
  );
}
