"""
LLM Service — explanation-only layer.

The LLM receives ONLY the structured output (priority, reason, recommended actions)
and rewrites it as natural, non-judgmental language.

It must NOT independently generate recommendations, scores, or diagnoses.
"""

import json
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import get_settings
from app.schemas.schemas import PriorityResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Priority's explanation assistant. Your ONLY job is to rewrite 
a structured health recommendation into friendly, natural language for a college student (18-25).

STRICT RULES:
1. You MUST only rephrase the provided recommendation. Do NOT invent new recommendations, 
   scores, diagnoses, or medical claims.
2. NEVER say things like "you have," "you are deficient in," "this means you have X," 
   "your risk of Y is Z%," or any diagnostic language.
3. Use a warm, non-judgmental, encouraging tone. No guilt, no fear-based language.
4. Keep it concise — 2-3 short sentences for the explanation, then list the actions.
5. Do NOT add disclaimers about consulting a doctor (the app handles that separately).
6. Do NOT mention AI, algorithms, scores, or how the recommendation was generated.
7. Address the user as "you" and keep language casual and relatable.

OUTPUT FORMAT: Return a plain text message, no markdown, no headers. Start with the 
explanation, then list the suggested actions as numbered items."""


async def generate_explanation(priority_result: PriorityResult) -> Optional[str]:
    """
    Use the LLM to rephrase the structured priority result into friendly language.

    Falls back to a template if the LLM call fails.

    Args:
        priority_result: the structured output from the priority engine.

    Returns:
        A natural-language explanation string, or a template fallback.
    """
    settings = get_settings()

    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key":
        logger.info("No OpenAI API key configured — using template fallback.")
        return _template_fallback(priority_result)

    user_message = (
        f"Priority dimension: {priority_result.priority_dimension.value}\n"
        f"Reason: {priority_result.priority_reason}\n"
        f"Suggested actions:\n"
    )
    for i, action in enumerate(priority_result.suggested_actions, 1):
        user_message += f"{i}. {action}\n"

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        explanation = response.choices[0].message.content.strip()

        # Basic safety check on LLM output
        if _contains_prohibited_content(explanation):
            logger.warning("LLM output contained prohibited content. Falling back to template.")
            return _template_fallback(priority_result)

        return explanation

    except Exception as e:
        logger.error(f"LLM call failed: {e}. Using template fallback.")
        return _template_fallback(priority_result)


def _template_fallback(priority_result: PriorityResult) -> str:
    """
    Template-based fallback when LLM is unavailable or fails.
    Still provides a useful, friendly message.
    """
    dim = priority_result.priority_dimension.value
    reason = priority_result.priority_reason

    message = f"Today, your top priority is {dim}. {reason}\n\nHere's what you can try:\n"
    for i, action in enumerate(priority_result.suggested_actions, 1):
        message += f"{i}. {action}\n"

    return message.strip()


def _contains_prohibited_content(text: str) -> bool:
    """
    Basic check for prohibited content in LLM output.
    Rejects responses that contain diagnostic or medical claim language.
    """
    text_lower = text.lower()
    prohibited_phrases = [
        "you have ",
        "you are deficient",
        "you are suffering from",
        "diagnosis",
        "diagnosed with",
        "your risk of",
        "risk percentage",
        "confidence score",
        "ai confidence",
        "medically",
        "clinical",
        "prescription",
        "you should see a doctor",
        "consult your physician",
    ]
    return any(phrase in text_lower for phrase in prohibited_phrases)
