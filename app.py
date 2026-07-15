"""
app.py
------
Trading News Dashboard -- Flask backend.

This server does two jobs only:
1. Serves the single HTML page (templates/index.html) plus static CSS/JS.
2. Exposes a small JSON API (/api/news) that the page's JavaScript calls
   to fetch live articles from MediaStack. The MediaStack API key never
   reaches the browser -- all requests to MediaStack happen server-side.

Run with:
    python app.py
"""

import os
import time

from flask import Flask, render_template, request, jsonify

from mediastack import fetch_news, MediaStackError
from utils import SECTION_CONFIG, MEDIASTACK_CATEGORIES, serialize_article

# Resolve template/static folders relative to THIS file's location, not the
# current working directory. This avoids 404s on static assets when the app
# is launched from a different folder (a common issue on Windows setups).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static",
)

# ---------------------------------------------------------------------------
# Very small in-memory cache so repeated requests (e.g. switching between
# sidebar tabs) don't hit the MediaStack API more than necessary.
# Keyed by the exact combination of query parameters; entries expire after
# CACHE_TTL_SECONDS. The "Refresh" button on the frontend sends
# ?refresh=1, which bypasses this cache and forces a live fetch.
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = 300
_cache: dict[tuple, tuple[float, list]] = {}


def cached_or_fresh_fetch(cache_key, force_refresh, **fetch_kwargs):
    now = time.time()

    if not force_refresh and cache_key in _cache:
        cached_at, cached_data = _cache[cache_key]
        if now - cached_at < CACHE_TTL_SECONDS:
            return cached_data

    data = fetch_news(**fetch_kwargs)
    _cache[cache_key] = (now, data)
    return data


@app.route("/")
def index():
    """Render the single-page dashboard shell."""
    return render_template(
        "index.html",
        sections=SECTION_CONFIG,
        section_names=list(SECTION_CONFIG.keys()),
        categories=MEDIASTACK_CATEGORIES,
    )


@app.route("/api/news")
def api_news():
    """
    JSON endpoint consumed by static/js/script.js.

    Query params:
        section   - one of the SECTION_CONFIG keys (default "Home")
        q         - free-text search query; overrides the section's
                    default keywords when present
        category  - MediaStack category to filter by (optional)
        date      - single date "YYYY-MM-DD" (optional)
        source    - comma separated source domains (optional)
        limit     - number of articles to return (default 25)
        refresh   - "1" to bypass the server-side cache
    """
    section = request.args.get("section", "Home")
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    date = request.args.get("date", "").strip()
    source = request.args.get("source", "").strip()
    limit = request.args.get("limit", "25")
    force_refresh = request.args.get("refresh", "0") == "1"

    try:
        limit = int(limit)
    except ValueError:
        limit = 25
    limit = max(1, min(limit, 100))

    section_config = SECTION_CONFIG.get(section, SECTION_CONFIG["Home"])

    # A typed search query always takes priority over the section default.
    if query:
        keywords = query
        categories = category or None
    else:
        keywords = section_config["keywords"]
        categories = category or section_config["categories"]

    cache_key = (section, query, category, date, source, limit)

    try:
        raw_articles = cached_or_fresh_fetch(
            cache_key,
            force_refresh,
            keywords=keywords,
            categories=categories,
            sources=source or None,
            date=date or None,
            limit=limit,
        )
    except MediaStackError as err:
        return jsonify({"success": False, "error": str(err), "articles": []}), 200

    articles = [serialize_article(a) for a in raw_articles]
    return jsonify({"success": True, "error": None, "articles": articles})


if __name__ == "__main__":
    # Startup diagnostics -- makes folder/path problems (a common cause of
    # 404s on style.css / script.js) immediately visible in the terminal.
    print("=" * 60)
    print("Trading News Dashboard -- starting up")
    print(f"Base directory:     {BASE_DIR}")
    print(f"Template directory: {TEMPLATE_DIR}  (exists: {os.path.isdir(TEMPLATE_DIR)})")
    print(f"Static directory:   {STATIC_DIR}  (exists: {os.path.isdir(STATIC_DIR)})")
    css_path = os.path.join(STATIC_DIR, "css", "style.css")
    js_path = os.path.join(STATIC_DIR, "js", "script.js")
    print(f"  css/style.css found:  {os.path.isfile(css_path)}")
    print(f"  js/script.js found:   {os.path.isfile(js_path)}")
    print("=" * 60)

    # debug=True is convenient for a college project; turn off in production.
    app.run(debug=True, port=5000)
