export interface BrandContact {
  name?: string;
  role?: string;
  email?: string;
  linkedin_url?: string;
}

export interface BrandCard {
  brand_name: string;
  last_sponsored_creator: string;
  last_sponsored_days_ago: number;
  contact: BrandContact;
  opener: string;
  source_videos: string[];
  last_campaign_snippet?: string;
}

export interface AgentReport {
  name: string;
  status: "idle" | "running" | "complete" | "failed";
  message: string;
  api_calls: Record<string, number>;
  error?: string;
}

export type PipelineStage =
  | "queued" | "discover" | "harvest" | "extract" | "enrich" | "draft"
  | "complete" | "error";

export interface JobStatus {
  job_id: string;
  stage: PipelineStage;
  message: string;
  progress: number;
  brands: BrandCard[];
  agent_reports: AgentReport[];
  api_calls: Record<string, number>;
  error?: string;
}
