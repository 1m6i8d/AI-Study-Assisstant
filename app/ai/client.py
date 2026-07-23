"""Shared Groq client, used by both the Quiz Generator and AI Tutor modules."""
import os
from groq import Groq

_client = None
DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set.")
        _client = Groq(api_key=api_key)
    return _client


def get_model():
    return os.environ.get("GROQ_MODEL", DEFAULT_MODEL)