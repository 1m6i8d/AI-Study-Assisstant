"""Flashcard model."""
from datetime import datetime

from app.extensions import db

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


class Flashcard(db.Model):
    __tablename__ = "flashcards"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)

    front = db.Column(db.String(500), nullable=False)
    back = db.Column(db.String(1000), nullable=False)
    difficulty = db.Column(db.String(10), nullable=True)  # null until first review

    review_count = db.Column(db.Integer, default=0, nullable=False)
    last_reviewed = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    subject = db.relationship(
        "Subject", backref=db.backref("flashcards", lazy="dynamic", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<Flashcard {self.id}>"