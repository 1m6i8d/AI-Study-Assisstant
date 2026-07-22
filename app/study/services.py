"""Business logic for study sessions, stats, and streaks."""
from datetime import datetime, timedelta

from app.extensions import db
from app.models.study_session import StudySession


def start_session(user_id, planned_minutes, subject_id=None):
    session = StudySession(user_id=user_id, subject_id=subject_id, planned_minutes=planned_minutes)
    db.session.add(session)
    db.session.commit()
    return session


def complete_session(session_id, user_id):
    """Mark a session complete. Enforces ownership. Returns None if not found or already completed."""
    session = StudySession.query.filter_by(id=session_id, user_id=user_id, completed=False).first()
    if session is None:
        return None
    session.completed_at = datetime.utcnow()
    session.completed = True
    db.session.commit()
    return session


def cancel_session(session_id, user_id):
    """Delete an incomplete (abandoned) session. Never deletes a completed one."""
    session = StudySession.query.filter_by(id=session_id, user_id=user_id, completed=False).first()
    if session:
        db.session.delete(session)
        db.session.commit()
        return True
    return False


def _completed_sessions(user_id):
    return StudySession.query.filter_by(user_id=user_id, completed=True).all()


def calculate_streak(completed_sessions):
    """Consecutive days (ending today or yesterday) with at least one completed session."""
    if not completed_sessions:
        return 0

    days_with_sessions = {s.completed_at.date() for s in completed_sessions if s.completed_at}
    streak = 0
    day = datetime.utcnow().date()

    # If nothing logged today yet, the streak is still "alive" as long as yesterday counts.
    if day not in days_with_sessions:
        day -= timedelta(days=1)

    while day in days_with_sessions:
        streak += 1
        day -= timedelta(days=1)

    return streak


def get_study_stats(user_id):
    """Aggregate stats: total/weekly/monthly hours, today's minutes, streak, completed count."""
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = datetime(now.year, now.month, 1)

    completed = _completed_sessions(user_id)

    total_minutes = sum(s.actual_minutes() or 0 for s in completed)
    weekly_minutes = sum(s.actual_minutes() or 0 for s in completed if s.completed_at >= week_start)
    monthly_minutes = sum(s.actual_minutes() or 0 for s in completed if s.completed_at >= month_start)
    today_minutes = sum(s.actual_minutes() or 0 for s in completed if s.completed_at >= today_start)

    return {
        "total_hours": round(total_minutes / 60, 1),
        "weekly_hours": round(weekly_minutes / 60, 1),
        "monthly_hours": round(monthly_minutes / 60, 1),
        "today_minutes": today_minutes,
        "streak": calculate_streak(completed),
        "completed_count": len(completed),
    }