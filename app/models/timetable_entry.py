"""TimetableEntry model — recurring weekly slots or one-off dated entries."""
from datetime import datetime

from app.extensions import db

ENTRY_TYPES = ["recurring", "one_off"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class TimetableEntry(db.Model):
    __tablename__ = "timetable_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True)

    title = db.Column(db.String(150), nullable=False)
    entry_type = db.Column(db.String(10), nullable=False)  # "recurring" or "one_off"

    day_of_week = db.Column(db.Integer, nullable=True)   # 0=Monday..6=Sunday, for recurring
    specific_date = db.Column(db.Date, nullable=True)    # for one_off

    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("timetable_entries", lazy="dynamic"))
    subject = db.relationship("Subject")

    def __repr__(self):
        return f"<TimetableEntry {self.title}>"