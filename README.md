# Prompt / LLM Playground

A focused workbench for prompt iteration, model configuration, structured output validation, run history and side-by-side comparison.

**Stack:** React, TypeScript, Python, FastAPI, SQLite

## Features

- **Prompt iteration** – system + user prompt editor, one-click run
- **Model configuration** – model name, temperature, top-p, max tokens
- **Structured output** – JSON mode with automatic validation and parse-error reporting
- **Compare** – run the same prompt under two configs in parallel (A vs B)
- **Inspect** – latency, token usage, finish reason and the exact request payload
- **History** – every run persisted in SQLite; restore any run back into the editor
- **Provider-agnostic** – works with any OpenAI-compatible API (OpenAI, Groq, Together, Ollama, LM Studio). With no API key set it falls back to a built-in mock provider, so the app runs fully offline.

## Run it

Backend (port 8000):

```bash
cd backend
pip install -r requirements.txt
# optional – real model:
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1   # or any compatible endpoint
uvicorn app.main:app --reload
```

Frontend (port 5173):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The header shows which provider is active (`mock` until a key is set).

## Tests

```bash
cd backend && python -m pytest
```

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/run` | Run one prompt with one config |
| POST | `/api/compare` | Run one prompt with configs A and B in parallel |
| GET | `/api/history` | List saved runs |
| GET/DELETE | `/api/history/{id}` | Fetch / delete a run |
| DELETE | `/api/history` | Clear history |
| GET | `/api/health` | Active provider |
