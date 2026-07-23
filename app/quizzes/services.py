"""Business logic for quiz storage, ownership, and scoring."""
import json

from app.extensions import db
from app.models.quiz import Quiz, QuizQuestion
from app.models.subject import Subject
from app.models.note import Note


def get_subject_notes_content(subject_id):
    """Concatenate all of a subject's note content, for use as quiz source material."""
    notes = Note.query.filter_by(subject_id=subject_id).all()
    return "\n\n".join(f"{n.title}\n{n.content}" for n in notes)


def create_quiz(subject_id, title, questions_data):
    quiz = Quiz(subject_id=subject_id, title=title, total_questions=len(questions_data))
    db.session.add(quiz)
    db.session.flush()  # get quiz.id before adding questions

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


def submit_quiz_answers(quiz_id, user_id, answers):
    """answers: dict of {question_id: answer_string}. Scores and marks the quiz completed."""
    from datetime import datetime

    quiz = get_quiz_or_404(quiz_id, user_id)
    correct_count = 0

    for question in quiz.questions:
        submitted = answers.get(str(question.id))
        question.user_answer = submitted
        if submitted and submitted.strip().lower() == question.correct_answer.strip().lower():
            correct_count += 1

    quiz.score = correct_count
    quiz.completed_at = datetime.utcnow()
    db.session.commit()
    return quiz