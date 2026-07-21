"""Business logic for note search, filtering, sorting, and ownership."""
from app.extensions import db
from app.models.note import Note
from app.models.subject import Subject

SORT_OPTIONS = {
    "updated_desc": (Note.updated_at.desc(), "Recently updated"),
    "updated_asc": (Note.updated_at.asc(), "Oldest updated"),
    "title_asc": (Note.title.asc(), "Title (A–Z)"),
    "title_desc": (Note.title.desc(), "Title (Z–A)"),
}
DEFAULT_SORT = "updated_desc"


def get_user_notes(user_id, search=None, subject_id=None, tag=None, sort=DEFAULT_SORT):
    """Return notes owned by a user (via subject), with optional filters."""
    query = Note.query.join(Subject).filter(Subject.user_id == user_id)

    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(Note.title.ilike(like), Note.content.ilike(like)))

    if subject_id:
        query = query.filter(Note.subject_id == subject_id)

    if tag:
        query = query.filter(Note.tags.ilike(f"%{tag}%"))

    order_clause, _ = SORT_OPTIONS.get(sort, SORT_OPTIONS[DEFAULT_SORT])
    return query.order_by(order_clause).all()


def get_note_or_404(note_id, user_id):
    """Fetch a note, enforcing ownership through its parent subject."""
    return (
        Note.query.join(Subject)
        .filter(Note.id == note_id, Subject.user_id == user_id)
        .first_or_404()
    )


def get_subject_choices(user_id):
    """Return (id, name) tuples for populating the subject SelectField."""
    subjects = Subject.query.filter_by(user_id=user_id).order_by(Subject.name.asc()).all()
    return [(s.id, s.name) for s in subjects]