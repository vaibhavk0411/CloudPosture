import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Server,
  Database,
  ShieldCheck,
  History,
  Cloud,
} from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", Icon: LayoutDashboard, end: true },
  { to: "/ec2", label: "EC2 Resources", Icon: Server },
  { to: "/s3", label: "S3 Buckets", Icon: Database },
  { to: "/security", label: "Security Checks", Icon: ShieldCheck },
  { to: "/scans", label: "Scan History", Icon: History },
];

export default function Sidebar() {
  return (
    <aside className="hidden md:flex md:w-64 shrink-0 flex-col bg-ink-900/60 border-r border-white/5 backdrop-blur">
      <div className="px-6 h-16 flex items-center gap-2.5 border-b border-white/5">
        <div className="p-2 rounded-lg bg-gradient-to-br from-brand-500 to-violet-600 shadow-glow">
          <Cloud className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-tight">
            CloudPosture
          </p>
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">
            Security Scanner
          </p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-brand-500/15 text-white border border-brand-500/30"
                  : "text-slate-400 hover:text-white hover:bg-white/5 border border-transparent"
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-white/5">
        <div className="card p-3 bg-gradient-to-br from-brand-500/10 to-violet-500/10 border-brand-500/20">
          <p className="text-xs font-semibold text-white">CIS Benchmark v1.5</p>
          <p className="text-[11px] text-slate-400 mt-1">
            AWS Foundations • 11 controls
          </p>
        </div>
      </div>
    </aside>
  );
}
