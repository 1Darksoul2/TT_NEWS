"""
mediastack.py
-------------
Handles all communication with the MediaStack News API.

MediaStack Docs: https://mediastack.com/documentation

This module intentionally contains NO Streamlit/Flask code, so it can be
tested or reused independently of the dashboard UI. It was named
`mediastack.py` (rather than `api.py`) specifically so it doesn't collide
with Vercel's required `api/` directory used for serverless functions.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
load_dotenv()

# Base endpoint for the MediaStack "news" resource.
# NOTE: The free MediaStack plan only supports HTTP (not HTTPS).
# If you are on a paid plan, you can switch this to "https://".
BASE_URL = "http://api.mediastack.com/v1/news"

# API key is read from the environment -- never hardcoded.
API_KEY = os.getenv("MEDIASTACK_API_KEY")


class MediaStackError(Exception):
    """Raised when the MediaStack API call fails for any reason."""
    pass


def fetch_news(
    keywords: str = None,
    categories: str = None,
    sources: str = None,
    countries: str = None,
    languages: str = "en",
    date: str = None,
    sort: str = "published_desc",
    limit: int = 25,
    offset: int = 0,
):
    """
    Fetch live news articles from the MediaStack API.

    Parameters
    ----------
    keywords : str, optional
        Search term(s). MediaStack supports boolean OR/-exclusion syntax,
        e.g. "Tesla OR Bitcoin" or "stocks -football".
    categories : str, optional
        Comma-separated MediaStack categories:
        general, business, entertainment, health, science, sports, technology.
    sources : str, optional
        Comma-separated source domains/ids to filter by, e.g. "bbc,cnn".
        Prefix with "-" to exclude a source.
    countries : str, optional
        Comma-separated ISO 3166 country codes, e.g. "in,us".
    languages : str, optional
        Comma-separated language codes. Defaults to English ("en").
    date : str, optional
        Single date "YYYY-MM-DD" or range "YYYY-MM-DD,YYYY-MM-DD".
    sort : str, optional
        One of: published_desc, published_asc, popularity.
    limit : int, optional
        Number of articles to return (MediaStack max is 100 per request).
    offset : int, optional
        Pagination offset, used for "load more" style pagination.

    Returns
    -------
    list[dict]
        A list of article dictionaries exactly as returned by MediaStack.
        Typical keys: author, title, description, url, source, image,
        category, language, country, published_at.

    Raises
    ------
    MediaStackError
        If the API key is missing, there is no internet connection,
        the request times out, or MediaStack returns an error payload.
    """

    if not API_KEY:
        raise MediaStackError(
            "MediaStack API key not found. Please add MEDIASTACK_API_KEY "
            "to your .env file (see .env example in the project root)."
        )

    # Build query params, only including optional filters when provided.
    params = {
        "access_key": API_KEY,
        "languages": languages,
        "sort": sort,
        "limit": limit,
        "offset": offset,
    }
    if keywords:
        params["keywords"] = keywords
    if categories:
        params["categories"] = categories
    if sources:
        params["sources"] = sources
    if countries:
        params["countries"] = countries
    if date:
        params["date"] = date

    # --- Make the request, translating network issues into friendly errors ---
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
    except requests.exceptions.ConnectionError:
        raise MediaStackError(
            "No internet connection detected. Please check your network and try again."
        )
    except requests.exceptions.Timeout:
        raise MediaStackError(
            "The request to MediaStack timed out. Please try again in a moment."
        )
    except requests.exceptions.RequestException as exc:
        raise MediaStackError(f"An unexpected network error occurred: {exc}")

    # MediaStack often returns HTTP 200 even on errors, so inspect the body too.
    try:
        payload = response.json()
    except ValueError:
        raise MediaStackError("Received an invalid (non-JSON) response from MediaStack.")

    if "error" in payload:
        message = payload["error"].get("message", "Unknown MediaStack error.")
        raise MediaStackError(f"MediaStack API error: {message}")

    if response.status_code != 200:
        raise MediaStackError(
            f"MediaStack API returned an unexpected status code: {response.status_code}."
        )

    return payload.get("data", [])
