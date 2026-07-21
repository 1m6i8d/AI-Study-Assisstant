"""Subject model."""
from datetime import datetime

from app.extensions import db

SUBJECT_COLORS = ["indigo", "teal", "amber", "rose", "slate", "emerald"]


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    color = db.Column(db.String(20), nullable=False, default="indigo")

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = db.relationship("User", backref=db.backref("subjects", lazy="dynamic"))

    # Populated once Notes/Flashcards/Quizzes/StudySessions models exist:
    # notes = db.relationship("Note", backref="subject", lazy="dynamic", cascade="all, delete-orphan")
    # flashcards = db.relationship("Flashcard", backref="subject", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject {self.name}>"