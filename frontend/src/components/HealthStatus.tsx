import { HealthResponse } from "../types";

interface HealthStatusProps {
  status: "ok" | "degraded" | "unknown";
  schemaTables?: string[];
}

export default function HealthStatus({ status }: HealthStatusProps) {
  const colorMap = {
    ok: "bg-emerald-400",
    degraded: "bg-amber-400",
    unknown: "bg-slate-500",
  };

  if (status === "unknown") {
    return (
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <div className="w-2 h-2 rounded-full bg-slate-500 animate-pulse" />
        Checking...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs">
      <div className={`w-2 h-2 rounded-full ${colorMap[status]} shadow-[0_0_6px_theme(colors.current)]`}>
        <span className="sr-only">{status}</span>
      </div>
      <span className={status === "ok" ? "text-emerald-400" : "text-amber-400"}>
        {status === "ok" ? "Backend connected" : "Backend degraded"}
      </span>
    </div>
  );
}
