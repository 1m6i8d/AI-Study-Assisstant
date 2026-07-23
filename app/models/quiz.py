"""Quiz and QuizQuestion models."""
import json
from datetime import datetime

from app.extensions import db

QUESTION_TYPES = ["multiple_choice", "true_false", "short_answer"]


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Integer, nullable=True)  # null until taken
    total_questions = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    subject = db.relationship(
        "Subject", backref=db.backref("quizzes", lazy="dynamic", cascade="all, delete-orphan")
    )
    questions = db.relationship(
        "QuizQuestion", backref="quiz", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Quiz {self.title}>"


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False, index=True)

    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    options_json = db.Column(db.Text, nullable=True)  # JSON list, null for short_answer
    correct_answer = db.Column(db.String(500), nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    user_answer = db.Column(db.String(500), nullable=True)

    def options(self):
        return json.loads(self.options_json) if self.options_json else []

    def is_correct(self):
        if self.user_answer is None:
            return None
        return self.user_answer.strip().lower() == self.correct_answer.strip().lower()

    def __repr__(self):
        return f"<QuizQuestion {self.id}>"