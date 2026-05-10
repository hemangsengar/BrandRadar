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
    ["YouTube search",   apiCalls.agentic_search  ?? 0],
    ["Video fetch",      apiCalls.scrape          ?? 0],
    ["Search API",       apiCalls.search          ?? 0],
    ["LinkedIn",         apiCalls.scrape_linkedin ?? 0],
    ["GPT-4o",          apiCalls.openai_gpt4o    ?? 0],
  ] as [string, number][]).filter(([, n]) => n > 0);

  return (
    <div
      className="fixed bottom-10 right-4 w-44 rounded-lg shadow-lg"
      style={{
        background: "#FFFFFF",
        border: "1px solid #E8E6E1",
        fontFamily: "var(--font-sans)",
        fontSize: "12px",
      }}
    >
      <div className="px-3 py-2.5" style={{ borderBottom: "1px solid #F0EDE8" }}>
        <span className="font-medium" style={{ color: "#0F0E0D" }}>API calls</span>
      </div>

      <div className="px-3 py-2 space-y-1.5">
        {rows.map(([label, n]) => (
          <div key={label} className="flex justify-between items-center">
            <span style={{ color: "#8C8780" }}>{label}</span>
            <span
              className="tabular-nums font-medium"
              style={{ color: "#0F0E0D", fontFamily: "var(--font-mono)", fontSize: "11px" }}
            >
              {n}
            </span>
          </div>
        ))}
      </div>

      {agentReports.length > 0 && (
        <div className="px-3 py-2" style={{ borderTop: "1px solid #F0EDE8", color: "#A09A94" }}>
          <span style={{ color: "#16A34A", fontWeight: 500 }}>{completed}</span>
          /{agentReports.length} agents
          {running > 0 && <span style={{ color: "#FF7A1A" }}> · {running} live</span>}
          {failed  > 0 && <span style={{ color: "#DC2626" }}> · {failed} failed</span>}
        </div>
      )}
    </div>
  );
}
