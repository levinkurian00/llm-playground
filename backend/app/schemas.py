from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = Field(0.7, ge=0, le=2)
    top_p: float = Field(1.0, ge=0, le=1)
    max_tokens: int = Field(512, ge=1, le=8192)
    output_format: Literal["text", "json"] = "text"


class RunRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system_prompt: str = ""
    config: ModelConfig = ModelConfig()


class CompareRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system_prompt: str = ""
    config_a: ModelConfig
    config_b: ModelConfig


class RunResult(BaseModel):
    id: Optional[int] = None
    provider: str
    model: str
    output: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str = "stop"
    json_valid: Optional[bool] = None
    parsed_json: Optional[Any] = None
    json_error: Optional[str] = None
    error: Optional[str] = None
    request: dict = {}


class CompareResult(BaseModel):
    a: RunResult
    b: RunResult


class HistoryItem(BaseModel):
    id: int
    created_at: str
    prompt: str
    system_prompt: str
    config: dict
    result: RunResult
