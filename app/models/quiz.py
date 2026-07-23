"""Quiz, QuizAttempt, and QuizQuestion models."""
import json
from datetime import datetime

from app.extensions import db

QUESTION_TYPES = ["multiple_choice", "true_false", "short_answer"]
MAX_ATTEMPTS_KEPT = 3


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    subject = db.relationship(
        "Subject", backref=db.backref("quizzes", lazy="dynamic", cascade="all, delete-orphan")
    )
    questions = db.relationship(
        "QuizQuestion", backref="quiz", lazy="dynamic", cascade="all, delete-orphan"
    )
    attempts = db.relationship(
        "QuizAttempt", backref="quiz", lazy="dynamic", cascade="all, delete-orphan",
        order_by="QuizAttempt.created_at.desc()",
    )

    def latest_attempt(self):
        return self.attempts.first()

    def __repr__(self):
        return f"<Quiz {self.title}>"


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False, index=True)

    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    options_json = db.Column(db.Text, nullable=True)
    correct_answer = db.Column(db.String(500), nullable=False)
    explanation = db.Column(db.Text, nullable=True)

    def options(self):
        return json.loads(self.options_json) if self.options_json else []

    def __repr__(self):
        return f"<QuizQuestion {self.id}>"


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False, index=True)

    score = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    answers = db.relationship(
        "QuizAttemptAnswer", backref="attempt", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<QuizAttempt {self.id} quiz={self.quiz_id}>"


class QuizAttemptAnswer(db.Model):
    __tablename__ = "quiz_attempt_answers"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempts.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_questions.id"), nullable=False)

    user_answer = db.Column(db.String(1000), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=True)  # AI/exact-match result
    manual_override = db.Column(db.Boolean, nullable=True)  # user's own correction, if flagged
    flagged = db.Column(db.Boolean, default=False, nullable=False)

    question = db.relationship("QuizQuestion")

    def final_correctness(self):
        """The override wins if present, otherwise the original grading."""
        return self.manual_override if self.manual_override is not None else self.is_correct

    def __repr__(self):
        return f"<QuizAttemptAnswer {self.id}>"