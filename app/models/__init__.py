"""Import all models here so Flask-Migrate can discover them via metadata."""
from app.models.user import User
from app.models.subject import Subject
from app.models.note import Note
from app.models.flashcard import Flashcard
from app.models.study_session import StudySession
from app.models.quiz import Quiz, QuizQuestion
from app.models.chat_history import ChatHistory
from app.models.timetable_entry import TimetableEntry

__all__ = [
    "User", "Subject", "Note", "Flashcard", "StudySession",
    "Quiz", "QuizQuestion", "ChatHistory", "TimetableEntry",
]