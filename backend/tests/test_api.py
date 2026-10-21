import os
import tempfile

os.environ["PLAYGROUND_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
client.__enter__()  # trigger startup (DB init)


def test_health_uses_mock_without_key():
    assert client.get("/api/health").json() == {"status": "ok", "provider": "mock"}


def test_run_text_and_history():
    r = client.post("/api/run", json={"prompt": "Explain recursion simply"})
    assert r.status_code == 200
    body = r.json()
    assert body["output"] and body["id"]
    assert body["total_tokens"] == body["prompt_tokens"] + body["completion_tokens"]
    hist = client.get("/api/history").json()
    assert any(h["id"] == body["id"] for h in hist)


def test_run_json_mode_validates():
    r = client.post("/api/run", json={"prompt": "Give me a summary", "config": {"output_format": "json"}})
    body = r.json()
    assert body["json_valid"] is True
    assert "summary" in body["parsed_json"]


def test_invalid_json_is_flagged():
    from app.main import validate_json_output
    from app.schemas import ModelConfig, RunResult

    bad = RunResult(provider="x", model="m", output="{oops", latency_ms=1,
                    prompt_tokens=1, completion_tokens=1, total_tokens=2)
    out = validate_json_output(bad, ModelConfig(output_format="json"))
    assert out.json_valid is False and out.json_error


def test_compare_runs_both_configs():
    r = client.post("/api/compare", json={
        "prompt": "Write a haiku about rain",
        "config_a": {"model": "model-a", "temperature": 0.2},
        "config_b": {"model": "model-b", "temperature": 1.5},
    })
    body = r.json()
    assert body["a"]["model"] == "model-a" and body["b"]["model"] == "model-b"
    assert body["a"]["output"] != body["b"]["output"]


def test_validation_rejects_bad_temperature():
    r = client.post("/api/run", json={"prompt": "hi", "config": {"temperature": 5}})
    assert r.status_code == 422


def test_delete_history():
    rid = client.post("/api/run", json={"prompt": "delete me"}).json()["id"]
    assert client.delete(f"/api/history/{rid}").status_code == 200
    assert client.get(f"/api/history/{rid}").status_code == 404
