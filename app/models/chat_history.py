"""ChatHistory model — stores AI Tutor conversation messages."""
import json
import uuid
from datetime import datetime

from app.extensions import db


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = db.Column(db.String(36), nullable=False, index=True)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=True)

    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    resources_json = db.Column(db.Text, nullable=True)  # {"videos": [...], "books": [...]}
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("chat_messages", lazy="dynamic"))
    note = db.relationship("Note")

    def resources(self):
        return json.loads(self.resources_json) if self.resources_json else None

    @staticmethod
    def new_conversation_id():
        return str(uuid.uuid4())

    def __repr__(self):
        return f"<ChatHistory {self.id} conv={self.conversation_id[:8]}>"