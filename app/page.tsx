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

  const isLoading = jobId !== null && status?.stage !== "complete" && status?.stage !== "error";
  const brands    = status?.brands ?? [];

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

  const inProgress = isLoading && status && !["queued", "complete", "error"].includes(status.stage);

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-950 to-zinc-900 text-white pb-16">
      <div className="max-w-5xl mx-auto px-4 py-16">

        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-orange-500/10 text-orange-400 text-xs font-medium px-3 py-1 rounded-full mb-6 border border-orange-500/20">
            Built at Anakin.io Mini-Hackathon · Bengaluru, May 2026
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold tracking-tight mb-4">
            Brand<span className="text-orange-500">Radar</span>
          </h1>
          <p className="text-zinc-400 text-xl max-w-xl mx-auto">
            Paste your YouTube channel URL. Get 25 brands ready to sponsor you tomorrow.
          </p>
          <p className="text-zinc-600 text-sm mt-2">
            For Indian creators with 5K–50K subs who don&apos;t have an agent.
          </p>
        </div>

        <SearchInput
          value={channelUrl}
          onChange={setChannelUrl}
          onSearch={handleSearch}
          isLoading={isLoading}
        />

        {inProgress && <ProgressTracker status={status!} className="mt-8" />}

        {isLoading && status?.stage === "queued" && (
          <p className="text-center text-zinc-500 text-sm mt-8 animate-pulse">
            Spinning up multi-agent pipeline…
          </p>
        )}

        {status?.stage === "error" && (
          <div className="mt-8 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-center text-sm">
            {status.message}
          </div>
        )}

        {brands.length > 0 && (
          <div className="mt-12">
            <div className="flex items-baseline gap-3 mb-6">
              <h2 className="text-xl font-semibold text-zinc-100">
                {brands.length} brands ready to sponsor you
              </h2>
              <span className="text-xs text-zinc-600">Click a card to reveal the pitch</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {brands.map((brand) => (
                <BrandCard key={brand.brand_name} brand={brand} />
              ))}
            </div>
          </div>
        )}
      </div>

      {status && (
        <ApiCounter
          apiCalls={status.api_calls ?? {}}
          agentReports={status.agent_reports ?? []}
        />
      )}
    </main>
  );
}
