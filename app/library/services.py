"""Business logic for saving and browsing library items."""
from app.extensions import db
from app.models.library_item import LibraryItem, ITEM_TYPES
from app.models.subject import Subject
from app.resources.external_apis import search_books_best_match, get_youtube_video_details, extract_youtube_video_id


def save_library_item(user_id, subject_id, item_type, title, url, thumbnail=None, creator=None, source="manual"):
    if item_type not in ITEM_TYPES or not title or not url or not subject_id:
        return None

    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
    if not subject:
        return None

    existing = LibraryItem.query.filter_by(subject_id=subject_id, url=url).first()
    if existing:
        return "duplicate"

    item = LibraryItem(
        user_id=user_id, subject_id=subject_id, item_type=item_type,
        title=title, url=url, thumbnail=thumbnail, creator=creator, source=source,
    )
    db.session.add(item)
    db.session.commit()
    return item


def add_manual_video(user_id, subject_id, youtube_url):
    video_id = extract_youtube_video_id(youtube_url)
    if not video_id:
        return None
    details = get_youtube_video_details(video_id)
    if not details:
        return None
    return save_library_item(
        user_id, subject_id, "video", details["title"], details["url"],
        thumbnail=details["thumbnail"], creator=details["channel"], source="manual",
    )


def add_manual_book(user_id, subject_id, title_query):
    match = search_books_best_match(title_query)
    if not match:
        return None
    return save_library_item(
        user_id, subject_id, "book", match["title"], match["url"],
        thumbnail=match["thumbnail"], creator=match["authors"], source="manual",
    )


def get_library_shelves(user_id):
    """One row per subject with item counts, for the shelf list view."""
    subjects = Subject.query.filter_by(user_id=user_id).all()
    return [(s, s.library_items.count()) for s in subjects]


def get_shelf_items(subject_id, user_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first_or_404()
    videos = LibraryItem.query.filter_by(subject_id=subject_id, item_type="video").order_by(LibraryItem.created_at.desc()).all()
    books = LibraryItem.query.filter_by(subject_id=subject_id, item_type="book").order_by(LibraryItem.created_at.desc()).all()
    return subject, videos, books


def delete_library_item(item_id, user_id):
    item = LibraryItem.query.join(Subject).filter(LibraryItem.id == item_id, Subject.user_id == user_id).first_or_404()
    db.session.delete(item)
    db.session.commit()