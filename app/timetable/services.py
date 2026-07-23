"""Business logic for timetable grid building, conflict detection, and ownership."""
from datetime import timedelta, datetime

from app.extensions import db
from app.models.timetable_entry import TimetableEntry

GRID_START_HOUR = 7
GRID_END_HOUR = 22
PIXELS_PER_MINUTE = 1  # 60px per hour


def get_entry_or_404(entry_id, user_id):
    return TimetableEntry.query.filter_by(id=entry_id, user_id=user_id).first_or_404()


def get_all_entries(user_id):
    return TimetableEntry.query.filter_by(user_id=user_id).all()


def _time_to_minutes(t):
    return t.hour * 60 + t.minute


def _entries_for_day(entries, day_date):
    """Return entries active on a specific calendar date: recurring entries matching
    that weekday, plus one_off entries matching that exact date."""
    weekday = day_date.weekday()
    day_entries = [
        e for e in entries
        if (e.entry_type == "recurring" and e.day_of_week == weekday)
        or (e.entry_type == "one_off" and e.specific_date == day_date)
    ]
    return sorted(day_entries, key=lambda e: e.start_time)


def _mark_conflicts(day_entries):
    """Pairwise overlap check within a single day's entries. Returns a set of conflicting entry IDs."""
    conflicting = set()
    for i, a in enumerate(day_entries):
        for b in day_entries[i + 1:]:
            if a.start_time < b.end_time and b.start_time < a.end_time:
                conflicting.add(a.id)
                conflicting.add(b.id)
    return conflicting


def build_week_grid(user_id, week_start):
    """week_start: a Monday date. Returns a list of 7 day dicts with positioned entries."""
    entries = get_all_entries(user_id)
    grid_start_minutes = GRID_START_HOUR * 60

    days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_entries = _entries_for_day(entries, day_date)
        conflicting_ids = _mark_conflicts(day_entries)

        positioned = []
        for e in day_entries:
            top = (_time_to_minutes(e.start_time) - grid_start_minutes) * PIXELS_PER_MINUTE
            height = (_time_to_minutes(e.end_time) - _time_to_minutes(e.start_time)) * PIXELS_PER_MINUTE
            positioned.append({
                "entry": e,
                "top": max(top, 0),
                "height": max(height, 20),  # minimum visible height
                "conflict": e.id in conflicting_ids,
            })

        days.append({"date": day_date, "entries": positioned})

    return days


def get_week_start(reference_date):
    """Return the Monday of the week containing reference_date."""
    return reference_date - timedelta(days=reference_date.weekday())