import { useState } from "react";
import type { ModelConfig, RunResult } from "./types";

export function ConfigPanel({
  config,
  onChange,
  title,
}: {
  config: ModelConfig;
  onChange: (c: ModelConfig) => void;
  title?: string;
}) {
  const set = <K extends keyof ModelConfig>(k: K, v: ModelConfig[K]) => onChange({ ...config, [k]: v });
  return (
    <div className="panel">
      {title && <div className="eyebrow">{title}</div>}
      <label>
        Model
        <input value={config.model} onChange={(e) => set("model", e.target.value)} />
      </label>
      <label>
        Temperature <span className="val">{config.temperature.toFixed(2)}</span>
        <input
          type="range" min={0} max={2} step={0.05} value={config.temperature}
          onChange={(e) => set("temperature", Number(e.target.value))}
        />
      </label>
      <label>
        Top-p <span className="val">{config.top_p.toFixed(2)}</span>
        <input
          type="range" min={0} max={1} step={0.05} value={config.top_p}
          onChange={(e) => set("top_p", Number(e.target.value))}
        />
      </label>
      <label>
        Max tokens
        <input
          type="number" min={1} max={8192} value={config.max_tokens}
          onChange={(e) => set("max_tokens", Math.max(1, Number(e.target.value) || 1))}
        />
      </label>
      <label>
        Output format
        <select value={config.output_format} onChange={(e) => set("output_format", e.target.value as "text" | "json")}>
          <option value="text">Text</option>
          <option value="json">Structured (JSON)</option>
        </select>
      </label>
    </div>
  );
}

export function ResultCard({ result, label }: { result: RunResult; label?: string }) {
  const [tab, setTab] = useState<"output" | "inspect">("output");
  return (
    <div className="panel result">
      <div className="result-head">
        {label && <span className="eyebrow">{label}</span>}
        <span className="tag">{result.model}</span>
        <span className="tag muted">{result.provider}</span>
        <div className="tabs small">
          <button className={tab === "output" ? "active" : ""} onClick={() => setTab("output")}>Output</button>
          <button className={tab === "inspect" ? "active" : ""} onClick={() => setTab("inspect")}>Inspect</button>
        </div>
      </div>

      {result.error ? (
        <div className="error">{result.error}</div>
      ) : tab === "output" ? (
        <>
          {result.json_valid !== null && (
            <div className={result.json_valid ? "badge ok" : "badge bad"}>
              {result.json_valid ? "Valid JSON" : `Invalid JSON — ${result.json_error}`}
            </div>
          )}
          <pre className="output">
            {result.json_valid ? JSON.stringify(result.parsed_json, null, 2) : result.output}
          </pre>
        </>
      ) : (
        <>
          <div className="stats">
            <Stat k="Latency" v={`${result.latency_ms} ms`} />
            <Stat k="Prompt tok" v={result.prompt_tokens} />
            <Stat k="Completion tok" v={result.completion_tokens} />
            <Stat k="Total tok" v={result.total_tokens} />
            <Stat k="Finish" v={result.finish_reason} />
          </div>
          <div className="eyebrow">Request payload</div>
          <pre className="output">{JSON.stringify(result.request, null, 2)}</pre>
        </>
      )}
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string | number }) {
  return (
    <div className="stat">
      <div className="k">{k}</div>
      <div className="v">{v}</div>
    </div>
  );
}
