"""
api/index.py
------------
Vercel entry point.

Vercel's Python runtime looks for a WSGI-compatible `app` object inside
files placed under the `api/` directory. Rather than duplicating the
whole Flask app here, we simply import the real app defined at the
project root (app.py) and re-export it -- so app.py stays the single
source of truth whether you run it locally with `python app.py` or
deploy it to Vercel.
"""

import os
import sys

# Make the project root importable, since app.py, mediastack.py, and
# utils.py live one directory above this file.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app  # noqa: E402  (import must follow the sys.path setup above)

# Vercel looks for this exact variable name.
__all__ = ["app"]
