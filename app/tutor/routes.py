"""AI Tutor chat routes."""
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user

from app.extensions import limiter
from app.models.chat_history import ChatHistory
from app.tutor.services import get_user_conversations, get_conversation_messages, send_message, delete_conversation
from app.notes.services import get_subject_choices
from app.models.note import Note
from app.models.subject import Subject
from app.library.services import save_library_item

import json as json_module

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
    subjects = get_subject_choices(current_user.id)
    subjects_json = json_module.dumps(subjects)
    return render_template(
        "tutor/chat.html", conversation_id=conversation_id, messages=messages,
        notes=notes, subjects_json=subjects_json)


@tutor_bp.route("/<conversation_id>/send", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def send(conversation_id):
    data = request.get_json(silent=True) or {}
    text = (data.get("message") or "").strip()
    note_id = data.get("note_id")

    if not text:
        return jsonify({"error": "Message cannot be empty."}), 400
    if len(text) > 2000:
        return jsonify({"error": "Message too long (max 2000 characters)."}), 400

    reply = send_message(current_user.id, conversation_id, text, note_id=note_id)
    return jsonify({
        "role": "assistant",
        "content": reply.content,
        "resources": reply.resources(),
        "message_id": reply.id,
    })

@tutor_bp.route("/save-resource", methods=["POST"])
@login_required
def save_resource():
    data = request.get_json(silent=True) or {}
    item = save_library_item(
        user_id=current_user.id,
        subject_id=data.get("subject_id"),
        item_type=data.get("item_type"),
        title=data.get("title"),
        url=data.get("url"),
        thumbnail=data.get("thumbnail"),
        creator=data.get("creator"),
        source="ai_suggested",
    )
    if item is None:
        return jsonify({"error": "Invalid data or subject not found."}), 400
    return jsonify({"saved": True, "duplicate": item == "duplicate"})

@tutor_bp.route("/<conversation_id>/delete", methods=["POST"])
@login_required
def delete(conversation_id):
    delete_conversation(conversation_id, current_user.id)
    flash("Conversation deleted.", "info")
    return redirect(url_for("tutor.index"))