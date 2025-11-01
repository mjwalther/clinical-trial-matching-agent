from __future__ import annotations
import os
import httpx
from typing import Callable, Tuple

def _getenv(key: str) -> str:
    val = os.environ.get(key)
    if val:
        return val
    # light .env read (if python-dotenv not used here)
    if os.path.exists(".env"):
        for line in open(".env"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == key:
                return v.strip()
    return ""

def get_lm(model_name: str = "gpt-4.1-mini", temperature: float = 0.2, max_tokens: int = 250) -> Callable[[str], Tuple[str, dict]]:
    """
    Returns a callable: text, meta = lm(prompt)

    Uses your course LiteLLM proxy directly via OpenAI-compatible /chat/completions.
    This avoids depending on the homework helper; if you have a HW wrapper, you can swap it in later.
    """
    api_base = _getenv("LITELLM_API_BASE")
    api_key = _getenv("LITELLM_API_KEY")
    if not api_base or not api_key:
        raise RuntimeError("Missing LITELLM_API_BASE or LITELLM_API_KEY in environment/.env")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = api_base.rstrip("/") + "/chat/completions"

    def _call(prompt: str):
        payload = {
            "model": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": "You are a concise, empathetic assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        with httpx.Client(timeout=60) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        text = data["choices"][0]["message"]["content"]
        return text, {"raw": data}

    return _call
