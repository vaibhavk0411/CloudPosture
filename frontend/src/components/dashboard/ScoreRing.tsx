interface Props {
  score: number; // 0-100
  size?: number;
  thickness?: number;
}

// Circular SVG progress ring used as the hero element on the dashboard.
// Color shifts from red → amber → emerald based on score.
export default function ScoreRing({ score, size = 160, thickness = 12 }: Props) {
  const safe = Math.max(0, Math.min(100, score));
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (safe / 100) * c;

  const color =
    safe >= 90 ? "#34d399" : safe >= 70 ? "#fbbf24" : "#f87171";
  const label = safe >= 90 ? "Excellent" : safe >= 70 ? "Acceptable" : "Needs Attention";

  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={thickness}
            fill="none"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke={color}
            strokeWidth={thickness}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.8s ease, stroke 0.4s" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold text-white">{safe.toFixed(0)}%</span>
          <span className="text-xs text-slate-400 mt-1">Compliance</span>
        </div>
      </div>
      <span
        className="badge mt-2"
        style={{ background: `${color}22`, color, border: `1px solid ${color}55` }}
      >
        {label}
      </span>
    </div>
  );
}
