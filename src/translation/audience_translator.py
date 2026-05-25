"""
audience_translator.py — Layer 6 audience-specific translation.

Consumes a per-building record (from labels.csv) plus optional Layer 2
precedents and Layer 3 narrative; produces an audience-specific text
output via Gemini 2.5 Flash with audience-tuned system instructions
and temperature.
"""

import os
from typing import Literal, Optional

from google import genai
from google.genai import types

from src.translation.bundle import format_bundle
from src.translation.prompts import AUDIENCE_CONFIG


def translate(
    record: dict,
    audience: Literal["insurance", "engineering", "legal"],
    precedents: Optional[list[dict]] = None,
    narrative: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
) -> dict:
    """Generate an audience-specific report for a building record.

    Returns a dict with the generated text plus the call parameters,
    so the audit chain captures what was sent and what came back.
    """
    if audience not in AUDIENCE_CONFIG:
        raise ValueError(f"Unknown audience: {audience}. Choose from {list(AUDIENCE_CONFIG)}.")

    cfg = AUDIENCE_CONFIG[audience]
    user_content = format_bundle(record, precedents=precedents, narrative=narrative)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=cfg["system_prompt"],
            temperature=cfg["temperature"],
            max_output_tokens=1024,
        ),
        contents=user_content,
    )

    return {
        "audience": audience,
        "model": model_name,
        "temperature": cfg["temperature"],
        "user_content": user_content,
        "output_text": response.text,
        # provenance fields for the audit chain
        "record_s_fid": record.get("s_fid") or record.get("id", "unknown"),
    }
