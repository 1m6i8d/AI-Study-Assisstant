"""Business logic for AI Tutor conversations and Groq chat calls."""
from app.extensions import db
from app.models.chat_history import ChatHistory
from app.models.note import Note
from app.ai.client import get_client, get_model

MAX_HISTORY_MESSAGES = 10  # caps token usage per request, per Groq free-tier TPM limits

TUTOR_SYSTEM_PROMPT = """You are a helpful, encouraging AI study tutor. You help students:
- Explain concepts clearly, with examples
- Summarize their notes
- Answer questions about what they're studying
- Suggest study techniques
- Explain programming concepts with code examples where useful
- Generate revision plans

Keep answers focused and practical. Use markdown formatting (bullet points, code blocks) where it helps clarity."""


def get_user_conversations(user_id):
    """Return one representative row per conversation, most recent first."""
    all_messages = (
        ChatHistory.query.filter_by(user_id=user_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    conversations = {}
    for msg in all_messages:
        conversations[msg.conversation_id] = msg  # last write wins -> most recent message per convo
    return sorted(conversations.values(), key=lambda m: m.created_at, reverse=True)


def get_conversation_messages(conversation_id, user_id):
    return (
        ChatHistory.query.filter_by(conversation_id=conversation_id, user_id=user_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )


def send_message(user_id, conversation_id, user_text, note_id=None):
    """Persist the user's message, call Groq with recent history, persist and return the reply."""
    history = get_conversation_messages(conversation_id, user_id)

    system_content = TUTOR_SYSTEM_PROMPT
    if note_id:
        note = Note.query.get(note_id)
        if note and note.subject.user_id == user_id:  # ownership check
            system_content += f"\n\nThe student has attached this note for context:\n\n{note.title}\n{note.content[:4000]}"

    # Persist user's message first
    user_msg = ChatHistory(
        user_id=user_id, conversation_id=conversation_id,
        note_id=note_id, role="user", content=user_text,
    )
    db.session.add(user_msg)
    db.session.commit()

    # Build the message list: system prompt + capped recent history + new message
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

    assistant_msg = ChatHistory(
        user_id=user_id, conversation_id=conversation_id,
        note_id=note_id, role="assistant", content=reply_text,
    )
    db.session.add(assistant_msg)
    db.session.commit()

    return assistant_msg