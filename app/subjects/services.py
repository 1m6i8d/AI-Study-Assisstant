"""Business logic for subject search, filtering, and sorting."""
from app.models.subject import Subject

SORT_OPTIONS = {
    "name_asc": (Subject.name.asc(), "Name (A–Z)"),
    "name_desc": (Subject.name.desc(), "Name (Z–A)"),
    "newest": (Subject.created_at.desc(), "Newest first"),
    "oldest": (Subject.created_at.asc(), "Oldest first"),
}
DEFAULT_SORT = "newest"


def get_user_subjects(user_id, search=None, color=None, sort=DEFAULT_SORT):
    """Return subjects for a user, optionally filtered by search term and color."""
    query = Subject.query.filter_by(user_id=user_id)

    if search:
        query = query.filter(Subject.name.ilike(f"%{search}%"))

    if color:
        query = query.filter_by(color=color)

    order_clause, _ = SORT_OPTIONS.get(sort, SORT_OPTIONS[DEFAULT_SORT])
    return query.order_by(order_clause).all()


def get_subject_or_404(subject_id, user_id):
    """Fetch a subject, enforcing ownership. Raises 404 if not found or not owned."""
    return Subject.query.filter_by(id=subject_id, user_id=user_id).first_or_404()