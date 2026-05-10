import { AgentReport } from "@/lib/types";
import { countByStatus } from "@/lib/utils";

interface Props {
  apiCalls: Record<string, number>;
  agentReports: AgentReport[];
}

export default function ApiCounter({ apiCalls, agentReports }: Props) {
  const total = Object.values(apiCalls).reduce((a, b) => a + b, 0);
  if (total === 0) return null;

  const { running, completed, failed } = countByStatus(agentReports);

  const rows = ([
    ["Agentic Search",      (apiCalls.agentic_search ?? 0)],
    ["URL Scrapes",         (apiCalls.scrape ?? 0) + (apiCalls.batch_scrape ?? 0)],
    ["LinkedIn Sessions",   (apiCalls.scrape_linkedin ?? 0)],
    ["Search API",          (apiCalls.search ?? 0)],
    ["GPT-4o Opener calls", (apiCalls.openai_gpt4o ?? 0)],
  ] as [string, number][]).filter(([, n]) => n > 0);

  return (
    <div className="fixed bottom-10 right-4 bg-zinc-900/95 backdrop-blur-sm border border-zinc-700 rounded-xl p-3.5 text-xs text-zinc-400 w-56 shadow-2xl">
      <p className="font-semibold text-zinc-200 mb-2 flex items-center gap-1.5">
        <span className="text-orange-400">◎</span> Anakin.io this run
      </p>
      <div className="space-y-1">
        {rows.map(([label, n]) => (
          <div key={label} className="flex justify-between">
            <span>{label}</span>
            <span className="text-zinc-300 font-medium tabular-nums">{n}×</span>
          </div>
        ))}
      </div>
      {agentReports.length > 0 && (
        <div className="mt-2.5 pt-2 border-t border-zinc-700/60 text-zinc-500">
          <span className="text-green-400">{completed}</span>/
          {agentReports.length} agents
          {running > 0 && <span className="text-orange-400"> · {running} running</span>}
          {failed  > 0 && <span className="text-red-400"> · {failed} failed</span>}
        </div>
      )}
    </div>
  );
}
