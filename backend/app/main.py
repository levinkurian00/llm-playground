import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .providers import Provider, get_provider
from .schemas import (
    CompareRequest, CompareResult, HistoryItem, ModelConfig, RunRequest, RunResult,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Prompt / LLM Playground", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_json_output(result: RunResult, cfg: ModelConfig) -> RunResult:
    """Structured-output check: does the model's reply parse as JSON?"""
    if cfg.output_format != "json" or result.error:
        return result
    try:
        result.parsed_json = json.loads(result.output)
        result.json_valid = True
    except json.JSONDecodeError as exc:
        result.json_valid = False
        result.json_error = f"{exc.msg} (line {exc.lineno}, col {exc.colno})"
    return result


async def _run_one(provider: Provider, prompt: str, system_prompt: str, cfg: ModelConfig) -> RunResult:
    result = await provider.complete(prompt, system_prompt, cfg)
    return validate_json_output(result, cfg)


def _persist(prompt: str, system_prompt: str, cfg: ModelConfig, result: RunResult) -> RunResult:
    result.id = db.save_run(prompt, system_prompt, cfg.model_dump(), result.model_dump())
    return result


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "provider": get_provider().name}


@app.post("/api/run", response_model=RunResult)
async def run(req: RunRequest) -> RunResult:
    result = await _run_one(get_provider(), req.prompt, req.system_prompt, req.config)
    return _persist(req.prompt, req.system_prompt, req.config, result)


@app.post("/api/compare", response_model=CompareResult)
async def compare(req: CompareRequest) -> CompareResult:
    provider = get_provider()
    a, b = await asyncio.gather(
        _run_one(provider, req.prompt, req.system_prompt, req.config_a),
        _run_one(provider, req.prompt, req.system_prompt, req.config_b),
    )
    return CompareResult(
        a=_persist(req.prompt, req.system_prompt, req.config_a, a),
        b=_persist(req.prompt, req.system_prompt, req.config_b, b),
    )


@app.get("/api/history", response_model=list[HistoryItem])
def history(limit: int = 50) -> list[dict]:
    return db.list_runs(limit)


@app.get("/api/history/{run_id}", response_model=HistoryItem)
def history_item(run_id: int) -> dict:
    item = db.get_run(run_id)
    if not item:
        raise HTTPException(404, "Run not found")
    return item


@app.delete("/api/history/{run_id}")
def delete_history_item(run_id: int) -> dict:
    if not db.delete_run(run_id):
        raise HTTPException(404, "Run not found")
    return {"deleted": run_id}


@app.delete("/api/history")
def clear_history() -> dict:
    db.clear_runs()
    return {"cleared": True}
