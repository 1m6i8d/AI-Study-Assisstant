"""StudySession model."""
from datetime import datetime

from app.extensions import db


class StudySession(db.Model):
    __tablename__ = "study_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True, index=True)

    planned_minutes = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", backref=db.backref("study_sessions", lazy="dynamic"))
    subject = db.relationship("Subject", backref=db.backref("study_sessions", lazy="dynamic"))

    def actual_minutes(self):
        """Actual elapsed minutes, or None if not yet completed."""
        if not self.completed_at:
            return None
        return round((self.completed_at - self.started_at).total_seconds() / 60)

    def __repr__(self):
        return f"<StudySession {self.id} user={self.user_id}>"