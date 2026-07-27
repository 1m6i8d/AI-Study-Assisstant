"""LibraryItem — user-saved videos and books, organized by subject."""
from datetime import datetime

from app.extensions import db

ITEM_TYPES = ["video", "book"]


class LibraryItem(db.Model):
    __tablename__ = "library_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)

    item_type = db.Column(db.String(10), nullable=False)  # "video" or "book"
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    thumbnail = db.Column(db.String(500), nullable=True)
    creator = db.Column(db.String(200), nullable=True)  # channel name or authors
    source = db.Column(db.String(20), default="manual", nullable=False)  # "ai_suggested" or "manual"

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    subject = db.relationship("Subject", backref=db.backref("library_items", lazy="dynamic", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<LibraryItem {self.title}>"