"""Business logic: keyword extraction, cache management, orchestration."""
import json
import time
from datetime import datetime

from app.extensions import db
from app.models.resource_cache import ResourceCache
from app.models.subject import Subject
from app.notes.services import get_subject_choices  # unused here, kept for parity if needed later
from app.quizzes.services import get_subject_notes_content
from app.ai.client import get_client, get_model
from app.resources.external_apis import search_youtube, search_books


def extract_keywords(content, max_keywords=3):
    """Use Groq to distill study content into concise search-friendly topic phrases."""
    if not content.strip():
        return []

    client = get_client()
    model = get_model()

    prompt = (
        f"Read these study notes and identify the {max_keywords} most important topics or concepts. "
        f"Respond with ONLY a comma-separated list of short search phrases (2-4 words each), "
        f"nothing else — no numbering, no explanation.\n\nNOTES:\n{content[:6000]}"
    )

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        keywords = [k.strip() for k in raw.split(",") if k.strip()]
        return keywords[:max_keywords]
    except Exception:
        return []


def get_resources_for_subject(subject_id, user_id, force_refresh=False):
    """Return cached or freshly-fetched video/book results for a subject."""
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first_or_404()

    cache = ResourceCache.query.filter_by(subject_id=subject_id).first()
    if cache and not cache.is_stale() and not force_refresh:
        return {
            "keywords": cache.keywords(),
            "videos": cache.videos(),
            "books": cache.books(),
            "cached": True,
            "fetched_at": cache.fetched_at,
        }

    content = get_subject_notes_content(subject_id)
    if not content.strip():
        return {"keywords": [], "videos": [], "books": [], "cached": False, "fetched_at": None}

    keywords = extract_keywords(content)
    if not keywords:
        keywords = [subject.name]  # fallback if extraction fails

    videos, books = [], []
    seen_video_ids, seen_book_titles = set(), set()

    for i, kw in enumerate(keywords[:2]):
        if i > 0:
            time.sleep(1)  # avoid tripping Books API burst rate limits between calls

        for v in search_youtube(kw, max_results=4):
            if v["video_id"] not in seen_video_ids:
                seen_video_ids.add(v["video_id"])
                videos.append(v)
        for b in search_books(kw, max_results=4):
            if b["title"] not in seen_book_titles:
                seen_book_titles.add(b["title"])
                books.append(b)

    videos = videos[:6]
    books = books[:6]

    if cache:
        cache.keywords_json = json.dumps(keywords)
        cache.videos_json = json.dumps(videos)
        cache.books_json = json.dumps(books)
        cache.fetched_at = datetime.utcnow()
    else:
        cache = ResourceCache(
            subject_id=subject_id,
            keywords_json=json.dumps(keywords),
            videos_json=json.dumps(videos),
            books_json=json.dumps(books),
        )
        db.session.add(cache)

    db.session.commit()

    return {"keywords": keywords, "videos": videos, "books": books, "cached": False, "fetched_at": cache.fetched_at}