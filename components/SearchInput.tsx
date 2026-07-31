"use client";

import { useRef, useState } from "react";

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
  const canSubmit = valid && !isLoading;
  const [shake, setShake] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    if (isLoading) return;
    if (!valid) {
      setShake(true);
      setTimeout(() => setShake(false), 500);
      inputRef.current?.focus();
      return;
    }
    onSearch();
  };

  return (
    <div
      className="relative max-w-xl mx-auto"
      style={{ filter: shake ? "none" : undefined }}
    >
      <div
        className="flex flex-col sm:flex-row rounded-xl overflow-hidden transition-all duration-200"
        style={{
          border: "1.5px solid",
          borderColor: value.length > 0 ? (valid ? "#FF7A1A" : "#E8E6E1") : "#E8E6E1",
          boxShadow: value.length > 0 && valid
            ? "0 0 0 4px rgba(255,122,26,0.10), 0 2px 16px rgba(0,0,0,0.06)"
            : "0 1px 4px rgba(0,0,0,0.04)",
          animation: shake ? "shake 0.4s ease-in-out" : undefined,
        }}
      >
        {/* URL prefix hint */}
        <div
          className="hidden sm:flex items-center pl-4 pr-1 shrink-0 select-none"
          style={{ background: "#FFFFFF" }}
        >
          <span
            className="text-sm"
            style={{ color: "#C4BFB9", fontFamily: "var(--font-sans)" }}
          >
            youtube.com/
          </span>
        </div>

        <input
          ref={inputRef}
          type="url"
          inputMode="url"
          autoCapitalize="none"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleClick()}
          placeholder="@yourchannel"
          disabled={isLoading}
          autoComplete="off"
          spellCheck={false}
          className="flex-1 h-14 px-4 sm:pl-0 outline-none bg-white text-sm"
          style={{
            fontFamily: "var(--font-sans)",
            color: "#0F0E0D",
            caretColor: "#FF7A1A",
          }}
        />

        <button
          onClick={handleClick}
          disabled={isLoading}
          className="h-14 px-4 sm:px-6 w-full sm:w-auto shrink-0 text-sm font-semibold transition-all duration-150 border-t sm:border-t-0 sm:border-l"
          style={{
            fontFamily: "var(--font-sans)",
            background: canSubmit ? "#FF7A1A" : isLoading ? "#FF7A1A" : "#F5F2ED",
            color: canSubmit || isLoading ? "#FFFFFF" : "#C4BFB9",
            cursor: isLoading ? "wait" : canSubmit ? "pointer" : "default",
            borderColor: canSubmit || isLoading ? "#FF7A1A" : "#E8E6E1",
          }}
        >
          {isLoading ? (
            <span className="flex items-center gap-2.5">
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-breath" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-breath" style={{ animationDelay: "200ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-breath" style={{ animationDelay: "400ms" }} />
              </span>
              Scanning
            </span>
          ) : (
            "Find brands →"
          )}
        </button>
      </div>

      {/* Inline validation hint */}
      {value.length > 0 && !valid && (
        <p
          className="text-xs mt-2 text-left pl-1 animate-fade-up"
          style={{ color: "#A09A94", fontFamily: "var(--font-sans)" }}
        >
          Paste a full channel URL like youtube.com/@yourchannel or just @handle
        </p>
      )}

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          20%       { transform: translateX(-6px); }
          40%       { transform: translateX(6px); }
          60%       { transform: translateX(-4px); }
          80%       { transform: translateX(4px); }
        }
      `}</style>
    </div>
  );
}
