"""Groq LLM integration for quiz generation."""
import json
import os
import re

from app.ai.client import get_client, get_model

SYSTEM_PROMPT = """You are a quiz generator. Given study notes, generate quiz questions.

Respond with ONLY valid JSON, no markdown fences, no preamble, no explanation outside the JSON.

Schema:
{
  "questions": [
    {
      "question_text": "string",
      "question_type": "multiple_choice" | "true_false" | "short_answer",
      "options": ["string", ...],   // only for multiple_choice (4 options) and true_false (["True", "False"]); omit for short_answer
      "correct_answer": "string",   // must exactly match one of the options for multiple_choice/true_false
      "explanation": "string"       // brief, 1-2 sentences, why this is correct
    }
  ]
}
"""


def _extract_json(raw_text):
    """Strip markdown code fences if the model added them despite instructions."""
    text = raw_text.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    return text


def generate_quiz(source_content, question_types, question_count):
    """Call Groq to generate quiz questions from source content.

    Returns a list of validated question dicts, or raises ValueError on failure.
    """
    if not source_content.strip():
        raise ValueError("No content available to generate a quiz from.")

    type_list = ", ".join(question_types)
    user_prompt = (
        f"Generate exactly {question_count} quiz questions from the following study notes. "
        f"Use only these question types: {type_list}. "
        f"Distribute question types roughly evenly if more than one type is requested.\n\n"
        f"STUDY NOTES:\n{source_content[:8000]}"  # cap input to stay within reasonable token usage
    )

    client = get_client()
    model = get_model()

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=0.7,
        )
    except Exception as exc:
        raise ValueError(f"AI request failed: {exc}") from exc

    raw_text = response.choices[0].message.content
    cleaned = _extract_json(raw_text)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI returned invalid JSON: {exc}") from exc

    questions = parsed.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("AI response did not contain a valid questions list.")

    validated = []
    for q in questions:
        if not all(k in q for k in ("question_text", "question_type", "correct_answer")):
            continue  # skip malformed entries rather than failing the whole batch
        if q["question_type"] not in ("multiple_choice", "true_false", "short_answer"):
            continue
        validated.append({
            "question_text": str(q["question_text"]).strip(),
            "question_type": q["question_type"],
            "options": q.get("options", []),
            "correct_answer": str(q["correct_answer"]).strip(),
            "explanation": str(q.get("explanation", "")).strip(),
        })

    if not validated:
        raise ValueError("AI response contained no valid questions after validation.")

    return validated