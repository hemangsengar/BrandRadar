"use client";

import { useState, useEffect, useRef } from "react";
import { JobStatus } from "@/lib/types";
import { cn, countByStatus } from "@/lib/utils";

const STAGES = [
  { key: "discover", label: "Discover" },
  { key: "harvest",  label: "Harvest"  },
  { key: "extract",  label: "Extract"  },
  { key: "enrich",   label: "Enrich"   },
  { key: "draft",    label: "Draft"    },
];

type LogEntry = { msg: string; id: number };
let _logId = 0;

export default function ProgressTracker({
  status,
  className,
}: {
  status: JobStatus;
  className?: string;
}) {
  const [log, setLog] = useState<LogEntry[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);
  const prevMsg = useRef<string>("");

  useEffect(() => {
    if (status.message && status.message !== prevMsg.current) {
      prevMsg.current = status.message;
      setLog((prev) => [...prev.slice(-24), { msg: status.message, id: ++_logId }]);
    }
  }, [status.message]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  const currentIdx = STAGES.findIndex((s) => s.key === status.stage);
  const { running, completed } = countByStatus(status.agent_reports ?? []);
  const totalAgents = (status.agent_reports ?? []).length;

  return (
    <div
      className={cn("rounded-xl overflow-hidden text-left", className)}
      style={{
        background: "#FFFFFF",
        border: "1.5px solid #E8E6E1",
        fontFamily: "var(--font-sans)",
        boxShadow: "0 2px 12px rgba(0,0,0,0.05)",
      }}
    >
      {/* Stage progress bar — connected dots */}
      <div className="px-5 pt-5 pb-4" style={{ borderBottom: "1px solid #F0EDE8" }}>
        <div className="flex items-center gap-0">
          {STAGES.map((s, i) => {
            const isDone   = i < currentIdx;
            const isActive = i === currentIdx;
            const isPending = i > currentIdx;
            return (
              <div key={s.key} className="flex items-center flex-1 last:flex-none">
                <div className="flex flex-col items-center gap-1.5">
                  <div
                    className="w-2.5 h-2.5 rounded-full shrink-0 transition-all duration-500"
                    style={{
                      background: isDone ? "#16A34A" : isActive ? "#FF7A1A" : "#E8E6E1",
                      boxShadow: isActive ? "0 0 0 3px rgba(255,122,26,0.2)" : undefined,
                    }}
                  />
                  <span
                    className="text-[10px] whitespace-nowrap transition-colors duration-300"
                    style={{
                      color: isDone ? "#16A34A" : isActive ? "#FF7A1A" : "#C4BFB9",
                      fontWeight: isActive ? 600 : 400,
                    }}
                  >
                    {s.label}
                  </span>
                </div>
                {i < STAGES.length - 1 && (
                  <div
                    className="flex-1 mx-1.5 transition-all duration-500"
                    style={{
                      height: "1.5px",
                      background: isDone
                        ? "linear-gradient(90deg, #16A34A, #BBF7D0)"
                        : isActive
                        ? "linear-gradient(90deg, #FF7A1A, #F0EDE8)"
                        : "#F0EDE8",
                      marginBottom: "14px",
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Animated progress bar */}
      <div className="relative" style={{ height: "3px", background: "#F5F2ED" }}>
        <div
          className="h-full transition-all duration-700 relative overflow-hidden"
          style={{ width: `${status.progress}%`, background: "#FF7A1A" }}
        >
          {/* Shine sweep */}
          <div
            className="absolute inset-y-0 w-8"
            style={{
              background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)",
              animation: "progress-shine 1.6s ease-in-out infinite",
            }}
          />
        </div>
      </div>

      {/* Live log */}
      <div
        className="px-5 py-4 space-y-1.5 max-h-36 overflow-y-auto"
        style={{ scrollbarWidth: "none" }}
      >
        {log.length === 0 && (
          <p className="text-sm" style={{ color: "#A09A94" }}>Initialising…</p>
        )}
        {log.map((entry, i) => {
          const isLast = i === log.length - 1;
          const age = log.length - 1 - i;
          const opacity = isLast ? 1 : age === 1 ? 0.55 : age === 2 ? 0.35 : 0.18;
          return (
            <p
              key={entry.id}
              className="text-sm leading-snug animate-slide-in"
              style={{
                color: "#0F0E0D",
                opacity,
                transition: "opacity 0.3s ease",
              }}
            >
              {entry.msg}
            </p>
          );
        })}
        {/* Blinking cursor */}
        {log.length > 0 && (
          <span
            className="inline-block w-1 h-3.5 align-middle animate-cursor"
            style={{ background: "#FF7A1A", opacity: 0.7 }}
          />
        )}
        <div ref={logEndRef} />
      </div>

      {/* Agent row */}
      {totalAgents > 0 && (
        <div
          className="px-5 py-3 flex items-center gap-4 text-xs"
          style={{ borderTop: "1px solid #F0EDE8", color: "#A09A94" }}
        >
          {/* Agent dots */}
          <div className="flex gap-1 flex-wrap">
            {(status.agent_reports ?? []).slice(0, 20).map((a, i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full transition-colors duration-300"
                style={{
                  background:
                    a.status === "completed" ? "#16A34A"
                    : a.status === "failed"    ? "#DC2626"
                    : a.status === "running"   ? "#FF7A1A"
                    : "#E8E6E1",
                  boxShadow: a.status === "running" ? "0 0 0 2px rgba(255,122,26,0.25)" : undefined,
                }}
                title={`${a.name}: ${a.status}`}
              />
            ))}
          </div>
          <span>
            <span style={{ color: "#16A34A", fontWeight: 500 }}>{completed}</span>
            /{totalAgents} done
          </span>
          {running > 0 && (
            <span style={{ color: "#FF7A1A" }}>{running} running</span>
          )}
          <span className="ml-auto tabular-nums" style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}>
            {status.progress}%
          </span>
        </div>
      )}
    </div>
  );
}
