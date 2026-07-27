"""Dashboard aggregation — welcome stats, today's schedule, flashcards due."""
from datetime import date, datetime

from app.study.services import get_study_stats
from app.timetable.services import get_all_entries
from app.models.flashcard import Flashcard
from app.models.subject import Subject

DUE_THRESHOLDS = {"hard": 3, "medium": 7, "easy": 14}


def get_today_timetable(user_id):
    today = date.today()
    weekday = today.weekday()
    entries = get_all_entries(user_id)
    todays = [
        e for e in entries
        if (e.entry_type == "recurring" and e.day_of_week == weekday)
        or (e.entry_type == "one_off" and e.specific_date == today)
    ]
    return sorted(todays, key=lambda e: e.start_time)


def get_due_flashcards(user_id, limit=5):
    """Heuristic due-list, not full spaced repetition — see Module 5's scope note."""
    cards = Flashcard.query.join(Subject).filter(Subject.user_id == user_id).all()
    now = datetime.utcnow()
    due = []
    for c in cards:
        if c.difficulty is None or c.last_reviewed is None:
            due.append(c)
            continue
        threshold_days = DUE_THRESHOLDS.get(c.difficulty, 7)
        if (now - c.last_reviewed).days >= threshold_days:
            due.append(c)
    return due[:limit]


def get_dashboard_data(user_id, daily_goal_minutes):
    stats = get_study_stats(user_id)
    goal_pct = 0
    if daily_goal_minutes:
        goal_pct = min(round((stats["today_minutes"] / daily_goal_minutes) * 100), 100)

    return {
        "today_minutes": stats["today_minutes"],
        "daily_goal_minutes": daily_goal_minutes,
        "goal_pct": goal_pct,
        "streak": stats["streak"],
        "today_timetable": get_today_timetable(user_id),
        "due_flashcards": get_due_flashcards(user_id),
    }