"""Direct wrappers around YouTube Data API v3 and Google Books API."""
import os
import time
import requests

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
BOOKS_SEARCH_URL = "https://www.googleapis.com/books/v1/volumes"


def search_youtube(query, max_results=5):
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return []

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key,
        "safeSearch": "moderate",
        "relevanceLanguage": "en",
    }

    try:
        response = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return []

    results = []
    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        results.append({
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
        })
    return results


def search_books(query, max_results=5, _retry=True):
    api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")
    params = {"q": query, "maxResults": max_results}
    if api_key:
        params["key"] = api_key

    try:
        response = requests.get(BOOKS_SEARCH_URL, params=params, timeout=8)
        if response.status_code == 503 and _retry:
            time.sleep(2)
            return search_books(query, max_results=max_results, _retry=False)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return []

    results = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        results.append({
            "title": info.get("title", "Untitled"),
            "authors": ", ".join(info.get("authors", [])) or "Unknown author",
            "thumbnail": info.get("imageLinks", {}).get("thumbnail", ""),
            "url": info.get("infoLink", ""),
            "description": (info.get("description", "") or "")[:200],
        })
    return results