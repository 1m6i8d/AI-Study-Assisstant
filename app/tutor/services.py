"""Business logic for AI Tutor conversations, Groq chat calls, and resource suggestions."""
import json
import re

from app.extensions import db
from app.models.chat_history import ChatHistory
from app.models.note import Note
from app.ai.client import get_client, get_model
from app.resources.external_apis import search_youtube, search_books
from app.resources.services import extract_keywords

MAX_HISTORY_MESSAGES = 10

TUTOR_SYSTEM_PROMPT = """You are a helpful, encouraging AI study tutor. You help students:
- Explain concepts clearly, with examples
- Summarize their notes
- Answer questions about what they're studying
- Suggest study techniques
- Explain programming concepts with code examples where useful
- Generate revision plans

Keep answers focused and practical. Use markdown formatting where it helps clarity."""

VIDEO_TRIGGERS = ("video", "youtube", "watch")
BOOK_TRIGGERS = ("book", "read", "textbook")
GENERIC_TRIGGERS = ("recommend", "suggest", "resource")


def _detect_resource_intent(text):
    lowered = text.lower()
    wants_videos = any(t in lowered for t in VIDEO_TRIGGERS)
    wants_books = any(t in lowered for t in BOOK_TRIGGERS)
    if not wants_videos and not wants_books and any(t in lowered for t in GENERIC_TRIGGERS):
        wants_videos = wants_books = True
    return wants_videos, wants_books


def _resolve_search_query(user_text, note):
    """Ground the search in the attached note's real content when possible;
    otherwise fall back to cleaning up the user's own phrasing."""
    if note:
        keywords = extract_keywords(note.content, max_keywords=2)
        if keywords:
            return " ".join(keywords)
        return note.title

    cleaned = user_text
    filler = VIDEO_TRIGGERS + BOOK_TRIGGERS + GENERIC_TRIGGERS + ("this", "topic", "on", "for", "about", "the")
    for word in filler:
        cleaned = re.sub(rf"\b{word}s?\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ?.!")
    return cleaned if len(cleaned) >= 3 else user_text


def get_user_conversations(user_id):
    all_messages = (
        ChatHistory.query.filter_by(user_id=user_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    conversations = {}
    for msg in all_messages:
        conversations[msg.conversation_id] = msg
    return sorted(conversations.values(), key=lambda m: m.created_at, reverse=True)


def get_conversation_messages(conversation_id, user_id):
    return (
        ChatHistory.query.filter_by(conversation_id=conversation_id, user_id=user_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )


def send_message(user_id, conversation_id, user_text, note_id=None):
    history = get_conversation_messages(conversation_id, user_id)

    note = None
    system_content = TUTOR_SYSTEM_PROMPT
    if note_id:
        candidate = Note.query.get(note_id)
        if candidate and candidate.subject.user_id == user_id:
            note = candidate
            system_content += f"\n\nThe student has attached this note for context:\n\n{note.title}\n{note.content[:4000]}"

    wants_videos, wants_books = _detect_resource_intent(user_text)
    if wants_videos or wants_books:
        system_content += (
            "\n\nThe student is asking for external resource recommendations. "
            "Real videos/books will be looked up separately and shown as cards below your reply. "
            "Do NOT invent or name specific video titles, channels, authors, or book titles yourself — "
            "any you make up will not match the real results shown and will confuse the student. "
            "Instead, write only a brief 1-2 sentence overview of the topic."
        )

    user_msg = ChatHistory(
        user_id=user_id, conversation_id=conversation_id,
        note_id=note_id, role="user", content=user_text,
    )
    db.session.add(user_msg)
    db.session.commit()

    recent = history[-MAX_HISTORY_MESSAGES:]
    messages = [{"role": "system", "content": system_content}]
    for msg in recent:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_text})

    client = get_client()
    model = get_model()

    try:
        response = client.chat.completions.create(messages=messages, model=model, temperature=0.7)
        reply_text = response.choices[0].message.content
    except Exception as exc:
        reply_text = f"Sorry, I couldn't process that right now. ({exc})"

    resources = None
    if wants_videos or wants_books:
        topic = _resolve_search_query(user_text, note)
        videos = search_youtube(topic, max_results=3) if wants_videos else []
        books = search_books(topic, max_results=3) if wants_books else []
        if videos or books:
            resources = {"videos": videos, "books": books}

    assistant_msg = ChatHistory(
        user_id=user_id, conversation_id=conversation_id,
        note_id=note_id, role="assistant", content=reply_text,
        resources_json=json.dumps(resources) if resources else None,
    )
    db.session.add(assistant_msg)
    db.session.commit()

    return assistant_msg

def delete_conversation(conversation_id, user_id):
    ChatHistory.query.filter_by(conversation_id=conversation_id, user_id=user_id).delete()
    db.session.commit()