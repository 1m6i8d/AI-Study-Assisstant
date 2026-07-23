"""AI Tutor chat routes."""
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user

from app.extensions import limiter
from app.models.chat_history import ChatHistory
from app.tutor.services import get_user_conversations, get_conversation_messages, send_message
from app.notes.services import get_subject_choices
from app.models.note import Note
from app.models.subject import Subject

tutor_bp = Blueprint("tutor", __name__, template_folder="../templates/tutor")


@tutor_bp.route("/")
@login_required
def index():
    conversations = get_user_conversations(current_user.id)
    return render_template("tutor/index.html", conversations=conversations)


@tutor_bp.route("/new")
@login_required
def new_conversation():
    conversation_id = ChatHistory.new_conversation_id()
    return redirect(url_for("tutor.conversation", conversation_id=conversation_id))


@tutor_bp.route("/<conversation_id>")
@login_required
def conversation(conversation_id):
    messages = get_conversation_messages(conversation_id, current_user.id)
    notes = (
        Note.query.join(Subject).filter(Subject.user_id == current_user.id)
        .order_by(Note.title.asc()).all()
    )
    return render_template(
        "tutor/chat.html", conversation_id=conversation_id, messages=messages, notes=notes
    )


@tutor_bp.route("/<conversation_id>/send", methods=["POST"])
@login_required
@limiter.limit("20 per minute")  # protects the shared Groq TPM/RPM budget
def send(conversation_id):
    data = request.get_json(silent=True) or {}
    text = (data.get("message") or "").strip()
    note_id = data.get("note_id")

    if not text:
        return jsonify({"error": "Message cannot be empty."}), 400
    if len(text) > 2000:
        return jsonify({"error": "Message too long (max 2000 characters)."}), 400

    reply = send_message(current_user.id, conversation_id, text, note_id=note_id)
    return jsonify({"role": "assistant", "content": reply.content})