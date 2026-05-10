"use client";

import { useState, useRef, useEffect } from "react";
import { BrandCard as BrandCardType } from "@/lib/types";

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="text-xs shrink-0 transition-all duration-150 px-2 py-0.5 rounded"
      style={{
        fontFamily: "var(--font-sans)",
        background: copied ? "rgba(22,163,74,0.08)" : "rgba(255,122,26,0.08)",
        color: copied ? "#16A34A" : "#FF7A1A",
        border: "1px solid",
        borderColor: copied ? "rgba(22,163,74,0.2)" : "rgba(255,122,26,0.2)",
      }}
    >
      {copied ? "✓ Copied" : "Copy"}
    </button>
  );
}

function PitchAccordion({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);

  useEffect(() => {
    if (contentRef.current) {
      setHeight(contentRef.current.scrollHeight);
    }
  }, [text]);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-sm transition-colors"
        style={{
          fontFamily: "var(--font-sans)",
          color: open ? "#8C8780" : "#FF7A1A",
        }}
      >
        <span
          className="transition-transform duration-200"
          style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)", display: "inline-block" }}
        >
          ›
        </span>
        {open ? "Hide pitch" : "Show pitch"}
      </button>

      <div
        className="overflow-hidden transition-all duration-300 ease-in-out"
        style={{ maxHeight: open ? `${height + 32}px` : "0px", opacity: open ? 1 : 0 }}
      >
        <div ref={contentRef}>
          <div
            className="mt-3"
            style={{
              background: "#FAFAF8",
              border: "1px solid #E8E6E1",
              borderLeft: "3px solid rgba(255,122,26,0.5)",
              borderRadius: "6px",
              padding: "14px 16px",
            }}
          >
            <p
              className="text-sm leading-relaxed mb-3"
              style={{ color: "#4A4744", fontFamily: "var(--font-sans)", lineHeight: "1.7" }}
            >
              {text}
            </p>
            <CopyBtn text={text} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BrandCard({ brand }: { brand: BrandCardType }) {
  const daysAgo = brand.last_sponsored_days_ago;
  const daysLabel = daysAgo >= 0 ? `${daysAgo}d ago` : "recently";
  const isRecent = daysAgo >= 0 && daysAgo <= 30;

  return (
    <div
      className="flex flex-col bg-white rounded-xl transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 animate-pop-in"
      style={{ border: "1.5px solid #E8E6E1" }}
    >
      {/* Header */}
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-start justify-between gap-3">
          <h3
            className="text-xl font-semibold leading-tight"
            style={{ fontFamily: "var(--font-sans)", color: "#0F0E0D" }}
          >
            {brand.brand_name}
          </h3>
          <div className="flex items-center gap-1.5 shrink-0 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#16A34A" }} />
            <span className="text-xs" style={{ color: "#16A34A", fontFamily: "var(--font-sans)" }}>
              active
            </span>
          </div>
        </div>

        {/* Last seen */}
        <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
          <p className="text-sm" style={{ color: "#8C8780", fontFamily: "var(--font-sans)" }}>
            Seen with <span style={{ color: "#0F0E0D", fontWeight: 500 }}>@{brand.last_sponsored_creator}</span>
          </p>
          <span
            className="text-xs px-1.5 py-0.5 rounded"
            style={{
              background: isRecent ? "rgba(22,163,74,0.08)" : "rgba(160,154,148,0.1)",
              color: isRecent ? "#16A34A" : "#8C8780",
              fontFamily: "var(--font-sans)",
            }}
          >
            {daysLabel}
          </span>
          {brand.source_videos[0] && (
            <a
              href={brand.source_videos[0]}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs transition-opacity hover:opacity-70"
              style={{ color: "#FF7A1A" }}
            >
              ↗ video
            </a>
          )}
        </div>
      </div>

      <div className="h-px mx-5" style={{ background: "#F0EDE8" }} />

      {/* Contact */}
      <div className="px-5 py-4 flex-1 space-y-2.5">
        {(brand.contact.name || brand.contact.role) && (
          <p className="text-sm" style={{ fontFamily: "var(--font-sans)" }}>
            {brand.contact.name && (
              <span style={{ color: "#0F0E0D", fontWeight: 500 }}>{brand.contact.name}</span>
            )}
            {brand.contact.role && (
              <span style={{ color: "#8C8780" }}> · {brand.contact.role}</span>
            )}
          </p>
        )}

        {brand.contact.email ? (
          <div className="flex items-center justify-between gap-3 rounded-lg px-3 py-2" style={{ background: "#FAFAF8", border: "1px solid #F0EDE8" }}>
            <span
              className="text-sm truncate"
              style={{ fontFamily: "var(--font-mono)", color: "#FF7A1A", fontSize: "12px" }}
            >
              {brand.contact.email}
            </span>
            <CopyBtn text={brand.contact.email} />
          </div>
        ) : (
          <p className="text-sm" style={{ color: "#C4BFB9", fontFamily: "var(--font-sans)" }}>
            No email found
          </p>
        )}

        {brand.contact.linkedin_url && (
          <a
            href={brand.contact.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs transition-opacity hover:opacity-70"
            style={{ color: "#818CF8", fontFamily: "var(--font-sans)" }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
            </svg>
            LinkedIn profile ↗
          </a>
        )}
      </div>

      {/* Pitch */}
      <div className="px-5 pb-5" style={{ borderTop: "1px solid #F0EDE8", paddingTop: "14px" }}>
        <PitchAccordion text={brand.opener} />
        {brand.source_videos.length > 1 && (
          <p className="text-xs mt-2" style={{ color: "#C4BFB9", fontFamily: "var(--font-sans)" }}>
            {brand.source_videos.length} sponsorship instances found
          </p>
        )}
      </div>
    </div>
  );
}
