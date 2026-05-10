"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BrandCard as BrandCardType } from "@/lib/types";

function CopyBtn({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="text-xs text-orange-400 hover:text-orange-300 font-medium transition-colors shrink-0"
    >
      {copied ? "Copied!" : label}
    </button>
  );
}

export default function BrandCard({ brand }: { brand: BrandCardType }) {
  const [open, setOpen] = useState(false);

  return (
    <Card className="bg-zinc-800/60 border-zinc-700 hover:border-zinc-600 transition-colors flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="font-bold text-white text-lg leading-tight truncate">
              {brand.brand_name}
            </h3>
            <Badge
              variant="outline"
              className="mt-1.5 text-xs border-green-500/25 text-green-400 bg-green-500/10"
            >
              last sponsored @{brand.last_sponsored_creator} {brand.last_sponsored_days_ago}d ago
            </Badge>
          </div>
          {brand.source_videos[0] && (
            <a
              href={brand.source_videos[0]}
              target="_blank"
              rel="noopener noreferrer"
              className="text-zinc-500 hover:text-zinc-300 text-xs shrink-0 mt-1"
            >
              View ↗
            </a>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 flex-1">
        <div className="bg-zinc-900/60 rounded-lg p-3 space-y-1.5">
          {(brand.contact.name || brand.contact.role) && (
            <p className="text-sm text-zinc-300">
              {brand.contact.name && <span className="font-medium">{brand.contact.name}</span>}
              {brand.contact.role && <span className="text-zinc-500"> · {brand.contact.role}</span>}
            </p>
          )}
          {brand.contact.email ? (
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-mono text-orange-300 truncate">{brand.contact.email}</p>
              <CopyBtn text={brand.contact.email} label="Copy" />
            </div>
          ) : (
            <p className="text-xs text-zinc-600">Email not found</p>
          )}
          {brand.contact.linkedin_url && (
            <a
              href={brand.contact.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-xs text-blue-400 hover:text-blue-300"
            >
              LinkedIn profile ↗
            </a>
          )}
        </div>

        <div className="flex items-center justify-between mb-1.5">
          <button
            onClick={() => setOpen(!open)}
            className="text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            {open ? "Hide pitch ↑" : "Show pitch ↓"}
          </button>
          {open && <CopyBtn text={brand.opener} label="Copy pitch" />}
        </div>
        {open && (
          <p className="text-sm text-zinc-300 leading-relaxed bg-zinc-900/40 rounded-lg p-3 border border-zinc-700/40">
            {brand.opener}
          </p>
        )}

        {brand.source_videos.length > 1 && (
          <p className="text-xs text-zinc-600">
            {brand.source_videos.length} sponsorship instances found
          </p>
        )}
      </CardContent>
    </Card>
  );
}
