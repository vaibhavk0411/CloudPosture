interface Props {
  rows?: number;
  className?: string;
}
// Simple skeleton loader to keep the dashboard feeling fast & polished
export default function Skeleton({ rows = 3, className = "" }: Props) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-4 rounded-md bg-white/5 animate-pulse"
          style={{ width: `${70 + Math.random() * 30}%` }}
        />
      ))}
    </div>
  );
}
