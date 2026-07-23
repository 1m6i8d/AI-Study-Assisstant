"""ResourceCache — stores YouTube/Books results per subject to respect API quotas."""
import json
from datetime import datetime, timedelta

from app.extensions import db

CACHE_TTL_HOURS = 24


class ResourceCache(db.Model):
    __tablename__ = "resource_cache"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True, unique=True)

    keywords_json = db.Column(db.Text, nullable=False)
    videos_json = db.Column(db.Text, nullable=False)
    books_json = db.Column(db.Text, nullable=False)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    subject = db.relationship("Subject", backref=db.backref("resource_cache", uselist=False, cascade="all, delete-orphan"))

    def is_stale(self):
        return datetime.utcnow() - self.fetched_at > timedelta(hours=CACHE_TTL_HOURS)

    def keywords(self):
        return json.loads(self.keywords_json)

    def videos(self):
        return json.loads(self.videos_json)

    def books(self):
        return json.loads(self.books_json)

    def __repr__(self):
        return f"<ResourceCache subject={self.subject_id}>"