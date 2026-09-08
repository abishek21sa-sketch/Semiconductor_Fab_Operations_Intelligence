"""FABOPS copilot: deterministic operational readout with optional Gemini narration."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

def status() -> dict[str, Any]:
    return {"provider": "Google Gemini", "model": DEFAULT_MODEL, "key_present": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")), "deterministic_fallback": True, "temperature": 0, "claim_boundary": "Virtual-fab and public-model outputs are review evidence; they do not authorize fab execution."}

def _deterministic(message: str, context: dict[str, Any]) -> str:
    q = message.casefold()
    if any(k in q for k in ("queue", "wait", "bottleneck", "amhs")):
        next_step = "Open Queue-Time Watch or AMHS Network, then compare the modeled queue-risk layer with the affected lot genealogy."
    elif any(k in q for k in ("yield", "wafer", "lot", "genealogy")):
        next_step = "Open Wafer Traceability or Yield / Rework and inspect the lot-level evidence before disposition."
    elif any(k in q for k in ("schedule", "release", "dispatch", "tool")):
        next_step = "Run the constrained schedule or Decision Center and review precedence, queue-time, reticle, and supervisor gates."
    elif any(k in q for k in ("model", "spc", "health", "provenance")):
        next_step = "Use Process Health and Public Model Provenance to separate measured/reference evidence from modeled estimates."
    else:
        next_step = "Start at Mission Control, drill into the relevant lot/tool/bay view, and keep the final action supervisor-gated."
    return ("Deterministic FABOPS operating readout\n\n" f"Question: {message.strip()}\n\n" f"Recommended path: {next_step}\n" f"Evidence: {context.get('evidence', 'reference virtual fab and governed analytics')}\n" "Boundary: no autonomous fab action is authorized; modeled values must be labeled as modeled.")

def _gemini(message: str, context: dict[str, Any]) -> str:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    body = {"system_instruction": {"parts": [{"text": "You are a semiconductor fab operations copilot. Deterministic schedule, queue, yield, SPC, and provenance outputs are authoritative. Never invent telemetry or authorize execution."}]}, "contents": [{"role": "user", "parts": [{"text": f"Context: {json.dumps(context, sort_keys=True)}\nQuestion: {message.strip()}"}]}], "generationConfig": {"temperature": 0, "seed": 42, "maxOutputTokens": 700}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_MODEL}:generateContent", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.loads(response.read().decode())
    text = "\n".join(p.get("text", "") for p in data.get("candidates", [{}])[0].get("content", {}).get("parts", []) if p.get("text"))
    if not text.strip():
        raise RuntimeError("Gemini returned no visible text")
    return text.strip()

def build_response(message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    fallback = _deterministic(message, context)
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        return {**status(), "answer": fallback, "provider": "deterministic", "model": "rule-based", "fallback": True}
    try:
        return {"answer": _gemini(message, context), "provider": "Google Gemini", "model": DEFAULT_MODEL, "fallback": False, **status()}
    except (OSError, urllib.error.URLError, json.JSONDecodeError, RuntimeError) as exc:
        return {**status(), "answer": fallback, "provider": "deterministic-fallback", "model": "rule-based", "fallback": True, "error": type(exc).__name__}
