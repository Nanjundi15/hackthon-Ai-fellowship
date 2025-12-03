# adapters/caption_llm_adapter.py
"""
Caption adapter using Google Generative REST API (text-bison-001).
- Uses GEMINI_API_KEY or GOOGLE_API_KEY from environment.
- Falls back to deterministic template captions if the REST call fails.
"""

import os
import requests
from typing import List

# Template fallback (guaranteed offline)
def _template_captions(brand, product, n):
    samples = [
        f"{brand} {product} — style meets performance.",
        f"Upgrade your day with the {product} from {brand}.",
        f"Feel the difference with {brand}'s {product}. Shop now!",
        f"The {product} by {brand} — crafted for comfort.",
        f"Special offer: grab the {product} by {brand} today."
    ]
    out = []
    idx = 0
    for i in range(n):
        out.append(samples[idx % len(samples)])
        idx += 1
    return out

# Env key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

class CaptionAdapter:
    def generate_captions(self, brand: str, product: str, n: int = 5) -> List[str]:
        raise NotImplementedError

class GeminiCaptionAdapter(CaptionAdapter):
    """
    Attempts a REST call to Google Generative Text API (text-bison-001).
    If it fails for any reason, falls back to template captions.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        # Base URL for Google Generative Text API (REST)
        self.url = "https://generativelanguage.googleapis.com/v1/models/text-bison-001:generate"

    def _call_rest(self, prompt: str, max_tokens: int = 200):
        if not self.api_key:
            raise RuntimeError("No GEMINI_API_KEY available")

        payload = {
            "prompt": {
                "text": prompt
            },
            # tuning options
            "maxOutputTokens": max_tokens,
            "temperature": 0.8,
        }

        try:
            resp = requests.post(self.url, params={"key": self.api_key}, json=payload, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            # Bubble up so caller can fallback
            raise RuntimeError(f"Generative REST call failed: {e}")

    def _extract_text_from_response(self, data):
        """
        Defensive parsing: different responses may include:
        - data['candidates'][0]['content']
        - data['candidates'][0]['output']
        - data['output'] (string)
        - or nested structures.
        """
        if not data:
            return None

        # 1) candidates list (common)
        if isinstance(data, dict):
            if "candidates" in data and isinstance(data["candidates"], list) and data["candidates"]:
                first = data["candidates"][0]
                if isinstance(first, dict):
                    # 'content' or 'output' keys
                    for key in ("content", "output", "text"):
                        if key in first and isinstance(first[key], str):
                            return first[key]
                elif isinstance(first, str):
                    return first

            # 2) direct 'output' or 'text' field
            for key in ("output", "text", "content"):
                if key in data and isinstance(data[key], str):
                    return data[key]

            # 3) nested: try to stringify common shapes
            # Look through dict values for a str
            for v in data.values():
                if isinstance(v, str) and len(v) > 10:
                    return v

        # last resort: stringify entire payload
        try:
            return str(data)
        except:
            return None

    def generate_captions(self, brand: str, product: str, n: int = 5) -> List[str]:
        # If no key present, fallback immediately
        if not self.api_key:
            return _template_captions(brand, product, n)

        prompt = (
            f"You are a senior performance marketer and copywriter. "
            f"Generate {n} short, punchy marketing captions (4-12 words) for this product. "
            f"Brand: {brand}. Product: {product}. Use active voice, include a short CTA, and return each caption on a new line."
        )

        try:
            data = self._call_rest(prompt, max_tokens=200)
            text = self._extract_text_from_response(data)
            if not text:
                return _template_captions(brand, product, n)

            # Split lines heuristically
            lines = [l.strip(" -•\n\r\t") for l in text.splitlines() if l.strip()]
            # If result is a single paragraph, try split by sentence punctuation
            if not lines:
                import re
                lines = [s.strip() for s in re.split(r'[\\.!;\\n]', text) if s.strip()]

            # If still not enough, pad with templates
            out = lines[:n]
            if len(out) < n:
                out.extend(_template_captions(brand, product, n - len(out)))
            return out[:n]
        except Exception as e:
            # On any failure, use templates (also print for server logs)
            print("Gemini REST caption error:", e)
            return _template_captions(brand, product, n)
