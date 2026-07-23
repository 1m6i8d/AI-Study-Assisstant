"""Business logic for quiz storage, attempts, grading, and flagging."""
import json
from datetime import datetime

from app.extensions import db
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAttemptAnswer, MAX_ATTEMPTS_KEPT
from app.models.subject import Subject
from app.models.note import Note
from app.quizzes.ai_service import judge_short_answer


def get_subject_notes_content(subject_id):
    notes = Note.query.filter_by(subject_id=subject_id).all()
    return "\n\n".join(f"{n.title}\n{n.content}" for n in notes)


def create_quiz(subject_id, title, questions_data):
    quiz = Quiz(subject_id=subject_id, title=title, total_questions=len(questions_data))
    db.session.add(quiz)
    db.session.flush()

    for q in questions_data:
        options_json = json.dumps(q["options"]) if q["options"] else None
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q["question_text"],
            question_type=q["question_type"],
            options_json=options_json,
            correct_answer=q["correct_answer"],
            explanation=q["explanation"],
        )
        db.session.add(question)

    db.session.commit()
    return quiz


def get_user_quizzes(user_id, subject_id=None):
    query = Quiz.query.join(Subject).filter(Subject.user_id == user_id)
    if subject_id:
        query = query.filter(Quiz.subject_id == subject_id)
    return query.order_by(Quiz.created_at.desc()).all()


def get_quiz_or_404(quiz_id, user_id):
    return (
        Quiz.query.join(Subject)
        .filter(Quiz.id == quiz_id, Subject.user_id == user_id)
        .first_or_404()
    )


def get_attempt_or_404(attempt_id, user_id):
    return (
        QuizAttempt.query.join(Quiz).join(Subject)
        .filter(QuizAttempt.id == attempt_id, Subject.user_id == user_id)
        .first_or_404()
    )


def start_attempt(quiz_id, user_id):
    """Create a new attempt, pruning the oldest if this would exceed MAX_ATTEMPTS_KEPT."""
    quiz = get_quiz_or_404(quiz_id, user_id)
    existing = quiz.attempts.order_by(QuizAttempt.created_at.asc()).all()

    if len(existing) >= MAX_ATTEMPTS_KEPT:
        oldest = existing[0]
        db.session.delete(oldest)

    attempt = QuizAttempt(quiz_id=quiz.id)
    db.session.add(attempt)
    db.session.commit()
    return attempt


def submit_attempt(attempt_id, user_id, answers):
    """answers: dict of {question_id_str: answer_string}. Grades and persists."""
    attempt = get_attempt_or_404(attempt_id, user_id)
    correct_count = 0

    for question in attempt.quiz.questions:
        submitted = answers.get(str(question.id))

        if question.question_type == "short_answer":
            is_correct = judge_short_answer(question.question_text, question.correct_answer, submitted)
        else:
            is_correct = bool(submitted) and submitted.strip().lower() == question.correct_answer.strip().lower()

        if is_correct:
            correct_count += 1

        db.session.add(QuizAttemptAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            user_answer=submitted,
            is_correct=is_correct,
        ))

    attempt.score = correct_count
    attempt.completed_at = datetime.utcnow()
    db.session.commit()
    return attempt


def toggle_flag(attempt_answer_id, user_id, override=None):
    """Flag an answer for review, optionally setting a manual correctness override."""
    answer = (
        QuizAttemptAnswer.query.join(QuizAttempt).join(Quiz).join(Subject)
        .filter(QuizAttemptAnswer.id == attempt_answer_id, Subject.user_id == user_id)
        .first_or_404()
    )
    answer.flagged = True
    if override is not None:
        answer.manual_override = override
        # Recalculate the attempt's score to reflect the correction
        attempt = answer.attempt
        attempt.score = sum(1 for a in attempt.answers if a.final_correctness())
    db.session.commit()
    return answer