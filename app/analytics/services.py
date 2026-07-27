"""Aggregation logic for the Analytics dashboard. Read-only — no new data stored."""
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.study_session import StudySession
from app.models.quiz import Quiz, QuizAttempt
from app.models.subject import Subject
from app.models.note import Note
from app.models.flashcard import Flashcard
from app.models.timetable_entry import TimetableEntry


def _last_n_days(n):
    today = datetime.utcnow().date()
    return [today - timedelta(days=i) for i in range(n - 1, -1, -1)]


def get_study_hours_series(user_id, days=14):
    """Minutes studied per day, last N days."""
    date_range = _last_n_days(days)
    start = datetime.combine(date_range[0], datetime.min.time())

    sessions = (
        StudySession.query
        .filter(StudySession.user_id == user_id, StudySession.completed == True)
        .filter(StudySession.completed_at >= start)
        .all()
    )

    minutes_by_day = defaultdict(int)
    for s in sessions:
        if s.completed_at:
            minutes_by_day[s.completed_at.date()] += (s.actual_minutes() or 0)

    return {
        "labels": [d.strftime("%b %d") for d in date_range],
        "values": [round(minutes_by_day.get(d, 0) / 60, 1) for d in date_range],
    }


def get_quiz_score_series(user_id, limit=15):
    """Score percentage per completed quiz attempt, chronological, most recent N."""
    attempts = (
        QuizAttempt.query.join(Quiz).join(Subject)
        .filter(Subject.user_id == user_id, QuizAttempt.completed_at.isnot(None))
        .order_by(QuizAttempt.completed_at.asc())
        .all()
    )
    attempts = attempts[-limit:]

    labels, values = [], []
    for a in attempts:
        total = a.quiz.total_questions or 1
        pct = round((a.score or 0) / total * 100)
        labels.append(a.completed_at.strftime("%b %d"))
        values.append(pct)

    return {"labels": labels, "values": values}


def get_subject_distribution(user_id):
    """Note count per subject — a simple proxy for where study content is concentrated."""
    subjects = Subject.query.filter_by(user_id=user_id).all()
    labels, values = [], []
    for s in subjects:
        count = Note.query.filter_by(subject_id=s.id).count()
        if count > 0:
            labels.append(s.name)
            values.append(count)
    return {"labels": labels, "values": values}


def get_flashcard_difficulty_breakdown(user_id):
    """Count of flashcards by difficulty, across all subjects."""
    cards = (
        Flashcard.query.join(Subject)
        .filter(Subject.user_id == user_id)
        .all()
    )
    counts = {"easy": 0, "medium": 0, "hard": 0, "unreviewed": 0}
    for c in cards:
        key = c.difficulty if c.difficulty in counts else "unreviewed"
        counts[key] += 1
    return {
        "labels": ["Easy", "Medium", "Hard", "Not reviewed"],
        "values": [counts["easy"], counts["medium"], counts["hard"], counts["unreviewed"]],
    }


def get_notes_created_series(user_id, days=14):
    date_range = _last_n_days(days)
    start = datetime.combine(date_range[0], datetime.min.time())

    notes = (
        Note.query.join(Subject)
        .filter(Subject.user_id == user_id, Note.created_at >= start)
        .all()
    )
    counts_by_day = defaultdict(int)
    for n in notes:
        counts_by_day[n.created_at.date()] += 1

    return {
        "labels": [d.strftime("%b %d") for d in date_range],
        "values": [counts_by_day.get(d, 0) for d in date_range],
    }


def get_planned_vs_actual(user_id, days=7):
    """For each of the last N days: planned minutes (from timetable entries active
    that day) vs. actual completed study minutes that day."""
    date_range = _last_n_days(days)
    entries = TimetableEntry.query.filter_by(user_id=user_id).all()

    sessions = (
        StudySession.query
        .filter(StudySession.user_id == user_id, StudySession.completed == True)
        .all()
    )
    actual_by_day = defaultdict(int)
    for s in sessions:
        if s.completed_at:
            actual_by_day[s.completed_at.date()] += (s.actual_minutes() or 0)

    planned_labels, planned_values, actual_values = [], [], []
    for d in date_range:
        weekday = d.weekday()
        planned_minutes = 0
        for e in entries:
            is_active = (
                (e.entry_type == "recurring" and e.day_of_week == weekday)
                or (e.entry_type == "one_off" and e.specific_date == d)
            )
            if is_active:
                start_m = e.start_time.hour * 60 + e.start_time.minute
                end_m = e.end_time.hour * 60 + e.end_time.minute
                planned_minutes += max(end_m - start_m, 0)

        planned_labels.append(d.strftime("%b %d"))
        planned_values.append(round(planned_minutes / 60, 1))
        actual_values.append(round(actual_by_day.get(d, 0) / 60, 1))

    return {"labels": planned_labels, "planned": planned_values, "actual": actual_values}


def get_summary_stats(user_id):
    total_notes = Note.query.join(Subject).filter(Subject.user_id == user_id).count()
    total_flashcards = Flashcard.query.join(Subject).filter(Subject.user_id == user_id).count()
    total_quizzes = Quiz.query.join(Subject).filter(Subject.user_id == user_id).count()

    completed_attempts = (
        QuizAttempt.query.join(Quiz).join(Subject)
        .filter(Subject.user_id == user_id, QuizAttempt.completed_at.isnot(None))
        .all()
    )
    avg_score = None
    if completed_attempts:
        pcts = [(a.score or 0) / (a.quiz.total_questions or 1) * 100 for a in completed_attempts]
        avg_score = round(sum(pcts) / len(pcts))

    total_study_minutes = sum(
        s.actual_minutes() or 0 for s in
        StudySession.query.filter_by(user_id=user_id, completed=True).all()
    )

    return {
        "total_notes": total_notes,
        "total_flashcards": total_flashcards,
        "total_quizzes": total_quizzes,
        "avg_quiz_score": avg_score,
        "total_study_hours": round(total_study_minutes / 60, 1),
    }