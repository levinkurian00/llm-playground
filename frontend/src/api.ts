import type { HistoryItem, ModelConfig, RunResult } from "./types";
const BASE = import.meta.env.VITE_API_URL ?? "";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; provider: string }>("/api/health"),
  run: (prompt: string, system_prompt: string, config: ModelConfig) =>
    request<RunResult>("/api/run", {
      method: "POST",
      body: JSON.stringify({ prompt, system_prompt, config }),
    }),
  compare: (prompt: string, system_prompt: string, config_a: ModelConfig, config_b: ModelConfig) =>
    request<{ a: RunResult; b: RunResult }>("/api/compare", {
      method: "POST",
      body: JSON.stringify({ prompt, system_prompt, config_a, config_b }),
    }),
  history: () => request<HistoryItem[]>("/api/history"),
  deleteRun: (id: number) => request<{ deleted: number }>(`/api/history/${id}`, { method: "DELETE" }),
  clearHistory: () => request<{ cleared: boolean }>("/api/history", { method: "DELETE" }),
};
