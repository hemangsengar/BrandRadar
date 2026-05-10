import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import type { AgentReport } from "@/lib/types"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function countByStatus(reports: AgentReport[]) {
  return {
    running:   reports.filter(a => a.status === "running").length,
    completed: reports.filter(a => a.status === "complete").length,
    failed:    reports.filter(a => a.status === "failed").length,
  };
}
