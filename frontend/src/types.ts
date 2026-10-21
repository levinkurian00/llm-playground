export interface ModelConfig {
  model: string;
  temperature: number;
  top_p: number;
  max_tokens: number;
  output_format: "text" | "json";
}

export interface RunResult {
  id: number | null;
  provider: string;
  model: string;
  output: string;
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  finish_reason: string;
  json_valid: boolean | null;
  parsed_json: unknown;
  json_error: string | null;
  error: string | null;
  request: Record<string, unknown>;
}

export interface HistoryItem {
  id: number;
  created_at: string;
  prompt: string;
  system_prompt: string;
  config: ModelConfig;
  result: RunResult;
}

export const DEFAULT_CONFIG: ModelConfig = {
  model: "llama-3.3-70b-versatile",
  temperature: 0.7,
  top_p: 1,
  max_tokens: 512,
  output_format: "text",
};
