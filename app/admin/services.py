"""Business logic for admin user management and platform overview."""
from app.extensions import db
from app.models.user import User
from app.models.subject import Subject
from app.models.note import Note
from app.models.flashcard import Flashcard
from app.models.quiz import Quiz, QuizAttempt
from app.models.study_session import StudySession
from app.models.chat_history import ChatHistory
from app.models.timetable_entry import TimetableEntry
from app.models.library_item import LibraryItem

SORT_COLUMNS = {
    "username": User.username,
    "email": User.email,
    "status": User.status,
    "created_at": User.created_at,
}


def get_pending_users():
    return User.query.filter_by(status="pending").order_by(User.created_at.asc()).all()


def get_all_users(search=None, sort="created_at", direction="desc"):
    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(User.username.ilike(like), User.email.ilike(like)))

    column = SORT_COLUMNS.get(sort, User.created_at)
    column = column.desc() if direction == "desc" else column.asc()

    # Admins always sort to the top, then the chosen sort applies within each group
    admin_priority = db.case((User.role == "admin", 0), else_=1)
    return query.order_by(admin_priority, column).all()


def get_user_stats():
    return {
        "total": User.query.count(),
        "pending": User.query.filter_by(status="pending").count(),
        "approved": User.query.filter_by(status="approved").count(),
        "suspended": User.query.filter_by(status="suspended").count(),
    }


def get_platform_stats():
    return {
        "total_subjects": Subject.query.count(),
        "total_notes": Note.query.count(),
        "total_flashcards": Flashcard.query.count(),
        "total_quizzes": Quiz.query.count(),
        "total_quiz_attempts": QuizAttempt.query.count(),
        "total_study_sessions": StudySession.query.filter_by(completed=True).count(),
        "total_chat_messages": ChatHistory.query.count(),
        "total_timetable_entries": TimetableEntry.query.count(),
        "total_library_items": LibraryItem.query.count(),
    }


def set_user_status(user_id, status):
    user = User.query.get_or_404(user_id)
    user.status = status
    db.session.commit()
    return user


def delete_user(user_id):
    """Permanently delete a user and everything they own. Subjects cascade to
    Notes/Flashcards/Quizzes/Library automatically; everything hanging directly
    off User is cleared explicitly first."""
    user = User.query.get_or_404(user_id)

    ChatHistory.query.filter_by(user_id=user.id).delete()
    StudySession.query.filter_by(user_id=user.id).delete()
    TimetableEntry.query.filter_by(user_id=user.id).delete()

    for subject in Subject.query.filter_by(user_id=user.id).all():
        db.session.delete(subject)

    db.session.delete(user)
    db.session.commit()