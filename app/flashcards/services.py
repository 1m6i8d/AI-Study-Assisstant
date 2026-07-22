"""Business logic for flashcard queries, ownership, and review ordering."""
from datetime import datetime

from app.extensions import db
from app.models.flashcard import Flashcard, DIFFICULTY_LEVELS
from app.models.subject import Subject

# Weighted so unreviewed and "hard" cards surface first in review mode
_DIFFICULTY_ORDER = {"hard": 0, "medium": 1, "easy": 2, None: -1}


def get_user_flashcards(user_id, subject_id=None, difficulty=None):
    """Return flashcards owned by a user (via subject), optionally filtered."""
    query = Flashcard.query.join(Subject).filter(Subject.user_id == user_id)

    if subject_id:
        query = query.filter(Flashcard.subject_id == subject_id)

    if difficulty:
        query = query.filter(Flashcard.difficulty == difficulty)

    return query.order_by(Flashcard.created_at.desc()).all()


def get_flashcard_or_404(flashcard_id, user_id):
    """Fetch a flashcard, enforcing ownership through its parent subject."""
    return (
        Flashcard.query.join(Subject)
        .filter(Flashcard.id == flashcard_id, Subject.user_id == user_id)
        .first_or_404()
    )


def get_review_queue(subject_id, user_id):
    """Return a subject's flashcards ordered for review: unreviewed and hard cards first."""
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first_or_404()
    cards = subject.flashcards.all()
    return sorted(cards, key=lambda c: _DIFFICULTY_ORDER.get(c.difficulty, -1))


def record_review(flashcard_id, user_id, difficulty):
    """Persist a review rating. Returns the updated flashcard or None if invalid."""
    if difficulty not in DIFFICULTY_LEVELS:
        return None

    card = get_flashcard_or_404(flashcard_id, user_id)
    card.difficulty = difficulty
    card.review_count += 1
    card.last_reviewed = datetime.utcnow()
    db.session.commit()
    return card