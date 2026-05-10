import { Progress } from "@/components/ui/progress";
import { JobStatus } from "@/lib/types";
import { cn, countByStatus } from "@/lib/utils";

const STAGES = [
  { key: "discover", label: "Discover" },
  { key: "harvest",  label: "Harvest"  },
  { key: "extract",  label: "Extract"  },
  { key: "enrich",   label: "Enrich"   },
  { key: "draft",    label: "Draft"    },
];

export default function ProgressTracker({
  status,
  className,
}: {
  status: JobStatus;
  className?: string;
}) {
  const currentIdx = STAGES.findIndex((s) => s.key === status.stage);
  const reports = status.agent_reports ?? [];
  const { running, completed } = countByStatus(reports);
  const runningAgents = reports.filter((a) => a.status === "running");

  return (
    <div className={cn("bg-zinc-800/50 border border-zinc-700 rounded-xl p-6", className)}>
      <div className="flex items-center gap-1 mb-5 flex-wrap">
        {STAGES.map((s, i) => {
          const isDone   = i < currentIdx;
          const isActive = i === currentIdx;
          return (
            <div key={s.key} className="flex items-center gap-1">
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  isDone
                    ? "bg-green-500/15 text-green-400 border-green-500/25"
                    : isActive
                    ? "bg-orange-500/15 text-orange-400 border-orange-500/25 animate-pulse"
                    : "bg-zinc-700/40 text-zinc-500 border-zinc-700"
                }`}
              >
                {isDone ? "✓ " : isActive ? "● " : "○ "}
                {s.label}
              </span>
              {i < STAGES.length - 1 && (
                <div className={`w-3 h-px ${i < currentIdx ? "bg-green-500/30" : "bg-zinc-700"}`} />
              )}
            </div>
          );
        })}
      </div>

      <Progress value={status.progress} className="h-1.5 mb-3 bg-zinc-700" />
      <p className="text-zinc-300 text-sm mb-2">{status.message}</p>

      {runningAgents.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {runningAgents.slice(0, 6).map((a) => (
            <span key={a.name} className="text-xs bg-zinc-700 text-zinc-300 px-2 py-0.5 rounded-full">
              ⚡ {a.name}
            </span>
          ))}
          {runningAgents.length > 6 && (
            <span className="text-xs text-zinc-500">+{runningAgents.length - 6} more</span>
          )}
        </div>
      )}

      {completed > 0 && (
        <p className="text-xs text-zinc-600 mt-2">
          {completed} of {reports.length} agents complete
        </p>
      )}
    </div>
  );
}
