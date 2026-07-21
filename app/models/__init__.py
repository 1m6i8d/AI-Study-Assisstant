"""Import all models here so Flask-Migrate can discover them via metadata."""
from app.models.user import User
from app.models.subject import Subject

__all__ = ["User", "Subject"]