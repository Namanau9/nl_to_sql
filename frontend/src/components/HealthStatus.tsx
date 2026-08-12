interface HealthStatusProps {
  status: "ok" | "degraded" | "unknown";
}

export default function HealthStatus({status}: HealthStatusProps) {
  const config = {
    ok: {dot: "bg-emerald-400", text: "text-emerald-500", label: "Connected"},
    degraded: {dot: "bg-amber-400", text: "text-amber-500", label: "Degraded"},
    unknown: {dot: "bg-slate-400 animate-pulse", text: "text-slate-400", label: "Checking..."},
  };

  const c = config[status];

  return (
    <div className="flex items-center gap-1.5 text-xs">
      <div className={`w-2 h-2 rounded-full ${c.dot}`} />
      <span className={c.text}>{c.label}</span>
    </div>
  );
}
