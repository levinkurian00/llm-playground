import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { ConfigPanel, ResultCard } from "./components";
import { DEFAULT_CONFIG, type HistoryItem, type ModelConfig, type RunResult } from "./types";

type Tab = "playground" | "compare" | "history";

export default function App() {
  const [tab, setTab] = useState<Tab>("playground");
  const [prompt, setPrompt] = useState("");
  const [system, setSystem] = useState("");
  const [config, setConfig] = useState<ModelConfig>(DEFAULT_CONFIG);
  const [configB, setConfigB] = useState<ModelConfig>({ ...DEFAULT_CONFIG, temperature: 1.2 });
  const [result, setResult] = useState<RunResult | null>(null);
  const [pair, setPair] = useState<{ a: RunResult; b: RunResult } | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState<string>("...");

  const loadHistory = useCallback(() => api.history().then(setHistory).catch(() => {}), []);

  useEffect(() => {
    api.health().then((h) => setProvider(h.provider)).catch(() => setProvider("offline"));
    loadHistory();
  }, [loadHistory]);

  const guard = async (fn: () => Promise<void>) => {
    if (!prompt.trim()) return setError("Write a prompt first.");
    setError(null);
    setLoading(true);
    try {
      await fn();
      loadHistory();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const run = () => guard(async () => setResult(await api.run(prompt, system, config)));
  const compare = () => guard(async () => setPair(await api.compare(prompt, system, config, configB)));

  const restore = (h: HistoryItem) => {
    setPrompt(h.prompt);
    setSystem(h.system_prompt);
    setConfig(h.config);
    setResult(h.result);
    setTab("playground");
  };

  return (
    <div className="app">
      <header>
        <div>
          <div className="eyebrow">PROJECT / 04 · DEVELOPER TOOL</div>
          <h1>Prompt / LLM Playground</h1>
        </div>
        <span className={`tag ${provider === "mock" ? "warn" : ""}`}>provider: {provider}</span>
      </header>

      <nav className="tabs">
        {(["playground", "compare", "history"] as Tab[]).map((t) => (
          <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
            {t}
            {t === "history" && history.length > 0 ? ` (${history.length})` : ""}
          </button>
        ))}
      </nav>

      {tab !== "history" && (
        <section className="editor">
          <div className="panel grow">
            <label>
              System prompt (optional)
              <textarea rows={2} value={system} onChange={(e) => setSystem(e.target.value)} placeholder="You are a helpful assistant..." />
            </label>
            <label>
              Prompt
              <textarea rows={6} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Type your prompt..." />
            </label>
            <button className="primary" disabled={loading} onClick={tab === "compare" ? compare : run}>
              {loading ? "Running..." : tab === "compare" ? "Compare A vs B" : "Run"}
            </button>
            {error && <div className="error">{error}</div>}
          </div>
          {tab === "playground" ? (
            <ConfigPanel config={config} onChange={setConfig} title="Configure" />
          ) : (
            <div className="col">
              <ConfigPanel config={config} onChange={setConfig} title="Config A" />
              <ConfigPanel config={configB} onChange={setConfigB} title="Config B" />
            </div>
          )}
        </section>
      )}

      {tab === "playground" && result && <ResultCard result={result} />}

      {tab === "compare" && pair && (
        <div className="split">
          <ResultCard result={pair.a} label="A" />
          <ResultCard result={pair.b} label="B" />
        </div>
      )}

      {tab === "history" && (
        <section>
          <div className="row">
            <div className="eyebrow">{history.length} saved runs</div>
            {history.length > 0 && (
              <button className="ghost" onClick={() => api.clearHistory().then(loadHistory)}>Clear all</button>
            )}
          </div>
          {history.length === 0 && <div className="panel muted">No runs yet.</div>}
          {history.map((h) => (
            <div className="panel history" key={h.id}>
              <div className="grow" onClick={() => restore(h)}>
                <div className="hist-prompt">{h.prompt}</div>
                <div className="muted small">
                  {new Date(h.created_at).toLocaleString()} · {h.config.model} · temp {h.config.temperature} · {h.result.total_tokens} tok · {h.result.latency_ms} ms
                </div>
              </div>
              <button className="ghost" onClick={() => api.deleteRun(h.id).then(loadHistory)}>Delete</button>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
