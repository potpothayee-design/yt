/** API data types mirroring the backend schemas. */

export interface User {
  id: number;
  email: string;
  name: string;
  is_admin: boolean;
}

export interface StepState {
  name: string;
  label: string;
  status: "pending" | "running" | "done" | "failed" | "skipped";
  message: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface Job {
  id: number;
  project_id: number;
  kind: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  runner: string;
  current_step: string | null;
  steps: StepState[] | null;
  error: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface Asset {
  id: number;
  project_id: number;
  kind: string;
  path: string;
  url: string;
  scene_index: number | null;
  duration: number | null;
  meta: Record<string, unknown> | null;
  created_at: string | null;
}

export interface Scene {
  index: number;
  type: string;
  focus: string;
  on_screen_text: string;
  narration: string;
  words?: number;
  planned_duration?: number;
}

export interface Script {
  title: string;
  topic: string;
  target_age: string;
  language: string;
  scenes: Scene[];
  learning_objectives?: string[];
  estimated_narration_seconds?: number;
}

export interface StoryboardScene {
  index: number;
  type: string;
  narration: string;
  visual_description: string;
  camera: string;
  motion: string;
  planned_duration: number;
  on_screen_text: string;
  character_action?: string;
}

export interface VideoMetadata {
  title?: string;
  description?: string;
  tags?: string[];
  hashtags?: string[];
  keywords?: string[];
  audience?: { made_for_kids: boolean; age_range: string };
  chapters?: { time: number | string; label: string }[];
  disclosure?: string;
  music_credits?: string;
}

export interface Project {
  id: number;
  topic: string;
  title: string;
  status:
    | "draft"
    | "generating"
    | "ready_for_review"
    | "failed"
    | "uploading"
    | "published";
  params: Record<string, unknown> | null;
  error: string | null;
  final_video_url: string | null;
  thumbnail_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ProjectDetail extends Project {
  knowledge: Record<string, unknown> | null;
  script: Script | null;
  storyboard: StoryboardScene[] | null;
  prompts: {
    character_sheet?: { name?: string; body_hex?: string; accessory?: string };
    negative_prompt?: string;
    scenes?: { image_prompt: string; video_prompt: string }[];
  } | null;
  video_metadata: VideoMetadata | null;
  assets: Asset[];
  latest_job: Job | null;
}

export interface UploadRecord {
  id: number;
  project_id: number;
  youtube_video_id: string | null;
  status: string;
  privacy: string;
  made_for_kids: boolean;
  scheduled_at: string | null;
  attempts: number;
  last_error: string | null;
  history: { time: string; status: string; message: string }[] | null;
  created_at: string | null;
}

export interface LogEntry {
  id: number;
  project_id: number | null;
  level: string;
  message: string;
  context: Record<string, unknown> | null;
  created_at: string | null;
}

export interface ProviderOption {
  name: string;
  label: string;
  requires_key: boolean;
  description: string;
}

export interface ProviderCapabilityState {
  selected: string;
  has_key: boolean;
  masked_key: string;
  options: Record<string, unknown>;
  available: ProviderOption[];
}

export interface ProviderSettings {
  capabilities: Record<string, ProviderCapabilityState>;
  youtube: { connected: boolean };
}

export interface YouTubeStatus {
  configured: boolean;
  connected: boolean;
  channel: string;
}

export interface TopicIdea {
  topic: string;
  example_age: string;
  description: string;
}
