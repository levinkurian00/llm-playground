"""LLM providers.

`OpenAICompatibleProvider` talks to any OpenAI-compatible /chat/completions
endpoint (OpenAI, Groq, Together, Ollama, LM Studio, ...). If no API key is
configured, `MockProvider` is used so the whole app still works offline.
"""
import hashlib
import json
import os
import time
from typing import Protocol

import httpx

from .schemas import ModelConfig, RunResult


class Provider(Protocol):
    name: str

    async def complete(self, prompt: str, system_prompt: str, cfg: ModelConfig) -> RunResult: ...


def _request_snapshot(prompt: str, system_prompt: str, cfg: ModelConfig) -> dict:
    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "max_tokens": cfg.max_tokens,
    }
    if cfg.output_format == "json":
        body["response_format"] = {"type": "json_object"}
    return body


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def complete(self, prompt: str, system_prompt: str, cfg: ModelConfig) -> RunResult:
        body = _request_snapshot(prompt, system_prompt, cfg)
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
            latency = int((time.perf_counter() - start) * 1000)
            if resp.status_code >= 400:
                return RunResult(
                    provider=self.name, model=cfg.model, output="", latency_ms=latency,
                    prompt_tokens=0, completion_tokens=0, total_tokens=0,
                    error=f"Provider returned {resp.status_code}: {resp.text[:300]}",
                    request=body,
                )
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return RunResult(
                provider=self.name,
                model=data.get("model", cfg.model),
                output=choice["message"]["content"] or "",
                latency_ms=latency,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
                request=body,
            )
        except httpx.HTTPError as exc:
            return RunResult(
                provider=self.name, model=cfg.model, output="",
                latency_ms=int((time.perf_counter() - start) * 1000),
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                error=f"Network error: {exc}", request=body,
            )


class MockProvider:
    """Deterministic fake model so the UI is fully usable without an API key."""

    name = "mock"

    async def complete(self, prompt: str, system_prompt: str, cfg: ModelConfig) -> RunResult:
        body = _request_snapshot(prompt, system_prompt, cfg)
        start = time.perf_counter()
        # Seed on prompt + model so A/B comparisons show visible differences.
        seed = int(hashlib.sha256(f"{cfg.model}|{prompt}".encode()).hexdigest(), 16)
        words = prompt.split()
        preview = " ".join(words[:12]) + ("..." if len(words) > 12 else "")

        if cfg.output_format == "json":
            text = json.dumps(
                {
                    "summary": f"Mock response to: {preview}",
                    "model": cfg.model,
                    "temperature": cfg.temperature,
                    "confidence": round(0.5 + (seed % 50) / 100, 2),
                },
                indent=2,
            )
        else:
            tone = "creative" if cfg.temperature > 1.0 else "balanced" if cfg.temperature > 0.4 else "precise"
            text = (
                f"[mock:{cfg.model}] A {tone} answer to: \"{preview}\"\n\n"
                "Set OPENAI_API_KEY (and optionally OPENAI_BASE_URL) to call a real model."
            )

        # Respect max_tokens roughly (1 token ~ 4 chars).
        limit = cfg.max_tokens * 4
        finish = "stop"
        if len(text) > limit:
            text, finish = text[:limit], "length"

        prompt_tokens = max(1, (len(prompt) + len(system_prompt)) // 4)
        completion_tokens = max(1, len(text) // 4)
        latency = int((time.perf_counter() - start) * 1000) + 120 + seed % 280
        return RunResult(
            provider=self.name, model=cfg.model, output=text, latency_ms=latency,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens, finish_reason=finish,
            request=body,
        )


def get_provider() -> Provider:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return OpenAICompatibleProvider(key, os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    return MockProvider()
