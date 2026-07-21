"""Import all models here so Flask-Migrate can discover them via metadata."""
from app.models.user import User
from app.models.subject import Subject
from app.models.note import Note

__all__ = ["User", "Subject", "Note"]