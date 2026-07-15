"""
utils.py
--------
Small, reusable helper functions used by the Flask backend:
- Formatting dates and descriptions for display
- Preparing article dicts for JSON responses
- Mapping sidebar sections to MediaStack search parameters

No frontend/UI framework code lives here -- this module is pure Python
and is shared only with app.py and api.py.
"""

from datetime import datetime

PLACEHOLDER_IMAGE = "https://via.placeholder.com/400x220.png?text=No+Image+Available"


def format_date(raw_date: str) -> str:
    """
    Convert MediaStack's ISO-8601 date string into a friendlier format.
    Example: '2026-07-15T10:32:00+00:00' -> 'Jul 15, 2026  10:32 AM'
    Falls back to the raw string if parsing fails.
    """
    if not raw_date:
        return "Unknown date"
    try:
        cleaned = raw_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt.strftime("%b %d, %Y  %I:%M %p")
    except (ValueError, TypeError):
        return raw_date


def truncate_text(text: str, max_length: int = 160) -> str:
    """Shorten a long description and append an ellipsis if needed."""
    if not text:
        return "No description available."
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def get_image(article: dict) -> str:
    """Return the article's image URL, or a placeholder if it has none."""
    image = article.get("image")
    return image if image else PLACEHOLDER_IMAGE


def serialize_article(article: dict) -> dict:
    """
    Normalize a raw MediaStack article into the exact shape the frontend
    JavaScript expects. Keeps all rendering/formatting logic server-side
    so the frontend stays simple (no date-math or truncation in JS).
    """
    return {
        "title": article.get("title") or "Untitled article",
        "description": truncate_text(article.get("description")),
        "url": article.get("url") or "",
        "image": get_image(article),
        "source": article.get("source") or "Unknown source",
        "category": (article.get("category") or "general").upper(),
        "published_at": article.get("published_at") or "",
        "published_display": format_date(article.get("published_at")),
    }


# ---------------------------------------------------------------------------
# Sidebar section -> MediaStack query mapping.
#
# MediaStack only offers these built-in categories: general, business,
# entertainment, health, science, sports, technology. It does NOT have
# finance-specific categories like "Banking" or "Auto", so those sidebar
# sections are implemented as targeted keyword searches instead, combined
# where useful with the closest matching MediaStack category.
# ---------------------------------------------------------------------------
SECTION_CONFIG = {
    "Home": {
        "keywords": None,
        "categories": "business",
        "icon": "home",
    },
    "Latest News": {
        "keywords": None,
        "categories": "general,business",
        "icon": "clock",
    },
    "Markets": {
        "keywords": "stock market,sensex,nifty,nasdaq,dow jones",
        "categories": None,
        "icon": "trending-up",
    },
    "Banking": {
        "keywords": "bank,banking,RBI,interest rate,NPA",
        "categories": None,
        "icon": "landmark",
    },
    "IT": {
        "keywords": "IT sector,software company,TCS,Infosys,Wipro",
        "categories": None,
        "icon": "cpu",
    },
    "Auto": {
        "keywords": "auto sector,automobile,electric vehicle,Tesla,Tata Motors",
        "categories": None,
        "icon": "car",
    },
    "Pharma": {
        "keywords": "pharma,pharmaceutical,drug approval,healthcare stocks",
        "categories": None,
        "icon": "pill",
    },
    "Energy": {
        "keywords": "energy sector,oil,natural gas,renewable energy",
        "categories": None,
        "icon": "zap",
    },
    "Commodities": {
        "keywords": "gold,silver,crude oil,commodities",
        "categories": None,
        "icon": "gem",
    },
    "Crypto": {
        "keywords": "bitcoin,cryptocurrency,ethereum,crypto market",
        "categories": None,
        "icon": "bitcoin",
    },
    "Economy": {
        "keywords": "economy,GDP,inflation,Fed,RBI policy",
        "categories": None,
        "icon": "bar-chart",
    },
    "Technology": {
        "keywords": None,
        "categories": "technology",
        "icon": "cpu",
    },
    "Politics": {
        "keywords": "politics,government,election,policy",
        "categories": "general",
        "icon": "flag",
    },
}

# MediaStack's own categories, used for the optional category filter.
MEDIASTACK_CATEGORIES = [
    "general",
    "business",
    "entertainment",
    "health",
    "science",
    "sports",
    "technology",
]
