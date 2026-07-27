"""Cross-module search across Subjects, Notes, and Flashcards."""
from app.models.subject import Subject
from app.models.note import Note
from app.models.flashcard import Flashcard


def global_search(user_id, query):
    query = (query or "").strip()
    if not query:
        return {"subjects": [], "notes": [], "flashcards": [], "query": query}

    like = f"%{query}%"

    subjects = (
        Subject.query.filter(Subject.user_id == user_id)
        .filter(Subject.name.ilike(like))
        .all()
    )

    notes = (
        Note.query.join(Subject)
        .filter(Subject.user_id == user_id)
        .filter((Note.title.ilike(like)) | (Note.content.ilike(like)))
        .all()
    )

    flashcards = (
        Flashcard.query.join(Subject)
        .filter(Subject.user_id == user_id)
        .filter((Flashcard.front.ilike(like)) | (Flashcard.back.ilike(like)))
        .all()
    )

    return {"subjects": subjects, "notes": notes, "flashcards": flashcards, "query": query}