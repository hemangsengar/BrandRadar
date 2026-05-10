"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface SearchInputProps {
  value: string;
  onChange: (v: string) => void;
  onSearch: () => void;
  isLoading: boolean;
}

function isValidYouTubeUrl(url: string): boolean {
  const cleaned = url.trim();
  return (
    cleaned.length > 0 &&
    (cleaned.includes("youtube.com/@") ||
      cleaned.includes("youtube.com/channel") ||
      cleaned.includes("youtube.com/c/") ||
      cleaned.startsWith("@"))
  );
}

export default function SearchInput({
  value,
  onChange,
  onSearch,
  isLoading,
}: SearchInputProps) {
  const valid = isValidYouTubeUrl(value);

  return (
    <div className="flex gap-3 max-w-2xl mx-auto">
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && valid && !isLoading && onSearch()}
        placeholder="youtube.com/@yourchannel"
        disabled={isLoading}
        className="h-12 text-base bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500 focus-visible:ring-orange-500"
      />
      <Button
        onClick={onSearch}
        disabled={!valid || isLoading}
        className="h-12 px-6 font-semibold whitespace-nowrap bg-orange-500 hover:bg-orange-600 text-white disabled:opacity-40"
      >
        {isLoading ? "Finding…" : "Find Brands"}
      </Button>
    </div>
  );
}
