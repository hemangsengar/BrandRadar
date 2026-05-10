"use client";

import { useState, useEffect, useRef } from "react";
import SearchInput from "@/components/SearchInput";
import ProgressTracker from "@/components/ProgressTracker";
import BrandCard from "@/components/BrandCard";
import ApiCounter from "@/components/ApiCounter";
import { JobStatus } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";
const POLL_MIN = 2000;
const POLL_MAX = 10000;

export default function Home() {
  const [channelUrl, setChannelUrl] = useState("");
  const [jobId, setJobId]           = useState<string | null>(null);
  const [status, setStatus]         = useState<JobStatus | null>(null);
  const pollRef                      = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intervalRef                  = useRef(POLL_MIN);
  const resultsRef                   = useRef<HTMLDivElement>(null);

  const isLoading = jobId !== null && status?.stage !== "complete" && status?.stage !== "error";
  const brands    = status?.brands ?? [];
  const hasResults = brands.length > 0;

  useEffect(() => {
    if (hasResults && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 200);
    }
  }, [hasResults]);

  const handleSearch = async () => {
    if (!channelUrl.trim() || isLoading) return;
    if (pollRef.current) clearTimeout(pollRef.current);
    setStatus(null);
    setJobId(null);
    intervalRef.current = POLL_MIN;

    try {
      const res = await fetch(`${API_BASE}/api/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel_url: channelUrl }),
      });
      if (!res.ok) throw new Error(`Start failed: ${res.status}`);
      const data = await res.json();
      setJobId(data.job_id);
    } catch (err) {
      console.error(err);
      setJobId(null);
    }
  };

  useEffect(() => {
    if (!jobId) return;

    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/status/${jobId}`);
        if (!res.ok) return;
        const data: JobStatus = await res.json();
        setStatus(data);
        if (data.stage === "complete" || data.stage === "error") return;
        intervalRef.current = Math.min(intervalRef.current * 1.4, POLL_MAX);
      } catch {}
      pollRef.current = setTimeout(poll, intervalRef.current);
    };

    pollRef.current = setTimeout(poll, POLL_MIN);
    return () => { if (pollRef.current) clearTimeout(pollRef.current); };
  }, [jobId]);

  const inProgress =
    isLoading && status && !["queued", "complete", "error"].includes(status.stage);

  const isIdle = !isLoading && !status;

  return (
    <main className="min-h-screen" style={{ background: "#FAFAF8" }}>

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Dot-grid texture */}
        <div
          className="absolute inset-0 pointer-events-none select-none"
          style={{
            backgroundImage: "radial-gradient(circle, #C8C4BE 1px, transparent 1px)",
            backgroundSize: "26px 26px",
            opacity: 0.35,
          }}
        />
        {/* Gradient fade at bottom */}
        <div
          className="absolute inset-x-0 bottom-0 h-40 pointer-events-none"
          style={{ background: "linear-gradient(to bottom, transparent, #FAFAF8)" }}
        />

        <div className="relative max-w-2xl mx-auto px-6 pt-20 pb-20 text-center">

          {/* Radar */}
          <div className="relative w-20 h-20 mx-auto mb-8 animate-fade-up">
            <div className="absolute inset-0 rounded-full" style={{ border: "1px solid #E8E6E1" }} />
            <div className="absolute inset-0 rounded-full overflow-hidden pointer-events-none">
              <div className="absolute top-1/2 left-0 right-0" style={{ height: "1px", background: "#F0EDE8" }} />
              <div className="absolute left-1/2 top-0 bottom-0" style={{ width: "1px", background: "#F0EDE8" }} />
            </div>
            <div className="absolute inset-0 rounded-full overflow-hidden pointer-events-none">
              <div
                className="absolute inset-0 animate-radar-sweep"
                style={{
                  background: "conic-gradient(from -90deg, transparent 70%, rgba(255,122,26,0.2) 92%, transparent 100%)",
                  transformOrigin: "center",
                }}
              />
            </div>
            <div className="absolute inset-0 rounded-full animate-radar"   style={{ border: "1px solid rgba(255,122,26,0.45)" }} />
            <div className="absolute inset-0 rounded-full animate-radar-2" style={{ border: "1px solid rgba(255,122,26,0.35)" }} />
            <div className="absolute inset-0 rounded-full animate-radar-3" style={{ border: "1px solid rgba(255,122,26,0.25)" }} />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: "#FF7A1A", boxShadow: "0 0 8px rgba(255,122,26,0.65)" }} />
            </div>
          </div>

          {/* Wordmark */}
          <h1
            className="text-5xl font-black tracking-tight leading-none mb-4 animate-fade-up delay-75"
            style={{ fontFamily: "var(--font-syne)", color: "#0F0E0D" }}
          >
            Brand<span style={{ color: "#FF7A1A" }}>Radar</span>
          </h1>

          {/* Value prop */}
          <p
            className="text-lg font-medium mb-2 animate-fade-up delay-150"
            style={{ color: "#0F0E0D", fontFamily: "var(--font-sans)" }}
          >
            Find brands actively sponsoring creators in your niche.
          </p>
          <p
            className="text-base mb-10 animate-fade-up delay-225"
            style={{ color: "#8C8780", fontFamily: "var(--font-sans)", lineHeight: "1.65" }}
          >
            We scan similar channels for active brand deals, find the right contact,
            and write you a personalised pitch — ready to send.
          </p>

          {/* Search — primary CTA */}
          <div className="animate-fade-up delay-300">
            <SearchInput
              value={channelUrl}
              onChange={setChannelUrl}
              onSearch={handleSearch}
              isLoading={isLoading}
            />
            <p className="text-xs mt-3" style={{ color: "#A09A94", fontFamily: "var(--font-sans)" }}>
              Built for Indian creators · works best with 5K–500K subscribers
            </p>
          </div>

          {/* How it works — only when idle */}
          {isIdle && (
            <div className="flex items-center justify-center gap-0 mt-10 animate-fade-up delay-400">
              {[
                { n: "1", label: "Paste your channel" },
                { n: "2", label: "We find similar creators" },
                { n: "3", label: "Get brands + pitches" },
              ].map((step, i) => (
                <div key={i} className="flex items-center">
                  <div className="flex items-center gap-2 px-3">
                    <span
                      className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-semibold shrink-0"
                      style={{ background: "rgba(255,122,26,0.1)", color: "#FF7A1A", fontFamily: "var(--font-sans)" }}
                    >
                      {step.n}
                    </span>
                    <span className="text-xs whitespace-nowrap" style={{ color: "#6B6760", fontFamily: "var(--font-sans)" }}>
                      {step.label}
                    </span>
                  </div>
                  {i < 2 && (
                    <div className="w-6 h-px" style={{ background: "#E8E6E1" }} />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Queued */}
          {isLoading && status?.stage === "queued" && (
            <p className="text-sm mt-10 animate-pulse" style={{ color: "#A09A94", fontFamily: "var(--font-sans)" }}>
              Starting analysis…
            </p>
          )}

          {/* Progress tracker */}
          {inProgress && <ProgressTracker status={status!} className="mt-10" />}

          {/* Error */}
          {status?.stage === "error" && (
            <div
              className="mt-10 px-5 py-4 text-sm text-center animate-fade-up rounded-xl"
              style={{
                background: "rgba(220,38,38,0.05)",
                border: "1.5px solid rgba(220,38,38,0.15)",
                color: "#DC2626",
                fontFamily: "var(--font-sans)",
              }}
            >
              {status.message}
            </div>
          )}
        </div>
      </section>

      {/* ── Results ──────────────────────────────────────────────────── */}
      {hasResults && (
        <div
          ref={resultsRef}
          className="border-t"
          style={{ borderColor: "#E8E6E1" }}
        >
          <div className="max-w-5xl mx-auto px-6 py-12 pb-28">

            {/* Results header */}
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
              <div>
                <h2
                  className="text-2xl font-semibold"
                  style={{ fontFamily: "var(--font-sans)", color: "#0F0E0D" }}
                >
                  {brands.length} brands found
                </h2>
                <p className="text-sm mt-1" style={{ color: "#8C8780", fontFamily: "var(--font-sans)" }}>
                  Actively sponsoring creators in your niche
                </p>
              </div>

              {/* Stats chips */}
              <div className="flex gap-2 flex-wrap">
                {(() => {
                  const emailCount = brands.filter(b => b.contact?.email).length;
                  const liCount    = brands.filter(b => b.contact?.linkedin_url).length;
                  return (
                    <>
                      {emailCount > 0 && (
                        <span
                          className="text-xs px-2.5 py-1 rounded-full"
                          style={{ background: "rgba(22,163,74,0.08)", color: "#16A34A", fontFamily: "var(--font-sans)", border: "1px solid rgba(22,163,74,0.15)" }}
                        >
                          {emailCount} emails found
                        </span>
                      )}
                      {liCount > 0 && (
                        <span
                          className="text-xs px-2.5 py-1 rounded-full"
                          style={{ background: "rgba(129,140,248,0.1)", color: "#818CF8", fontFamily: "var(--font-sans)", border: "1px solid rgba(129,140,248,0.2)" }}
                        >
                          {liCount} on LinkedIn
                        </span>
                      )}
                    </>
                  );
                })()}
                <span
                  className="text-xs px-2.5 py-1 rounded-full"
                  style={{ background: "rgba(255,122,26,0.08)", color: "#FF7A1A", fontFamily: "var(--font-sans)", border: "1px solid rgba(255,122,26,0.15)" }}
                >
                  {brands.length} pitches ready
                </span>
              </div>
            </div>

            {/* Cards grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {brands.map((brand, i) => (
                <div
                  key={brand.brand_name}
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <BrandCard brand={brand} />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* API counter widget */}
      {status && (
        <ApiCounter
          apiCalls={status.api_calls ?? {}}
          agentReports={status.agent_reports ?? []}
        />
      )}
    </main>
  );
}
