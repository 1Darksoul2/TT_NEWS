# 📈 Trading News Dashboard (Flask + HTML/CSS/JS)

A clean, simple **Python-only backend** dashboard for traders to browse live
financial news. The backend is **Flask**; the frontend is plain
**HTML, CSS, and vanilla JavaScript** -- no React, no Next.js, no Node.js,
and no JavaScript frameworks of any kind.

There is **no AI, no sentiment analysis, and no summarization** in this
project. Every headline, description, image, and link comes directly and
only from the live [MediaStack News API](https://mediastack.com/).

---

## ✨ Features

- **Sidebar navigation** across Home, Latest News, Markets, Banking, IT,
  Auto, Pharma, Energy, Commodities, Crypto, Economy, Technology, Politics,
  and Saved Articles.
- **Live search** by company, stock, keyword, or sector (e.g. Reliance,
  TCS, Infosys, Gold, Oil, Bitcoin, Nifty, RBI, Fed, Tesla, Apple).
- **Filters** for category, date, source, and result count.
- **Refresh button** that bypasses the server cache and force-fetches
  the latest news.
- **Bookmarking that persists across page reloads**, using the browser's
  `localStorage` -- view them on a dedicated "Saved Articles" page.
- **Card-based, responsive grid layout** with images, headlines,
  descriptions, source, published date, category badge, and a
  "Read Full Article" link.
- **Modern, distinctive styling**: dark navy sidebar, rounded white cards
  with soft shadows, a blue accent color, and a monospace type treatment
  for data/meta fields (source, date, category) for a ticker-tape feel.
- **Friendly error handling** for failed requests, empty results, or no
  internet connection -- surfaced directly in the page, not just the console.

---

## 📁 Project Structure

```
TradingNewsDashboardHTML/
│── app.py                 # Flask app: serves the page + /api/news JSON endpoint
│── api.py                 # MediaStack API wrapper (all HTTP calls happen here)
│── utils.py                # Formatting helpers + section/category config
│── templates/
│   └── index.html           # Single-page HTML shell (Jinja2 template)
│── static/
│   ├── css/style.css        # All custom styling
│   └── js/script.js         # All frontend behaviour (vanilla JS, no frameworks)
│── requirements.txt          # Python dependencies
│── .env                       # Your API key (NOT committed to version control)
│── README.md                   # This file
└── assets/                      # Optional local images/icons
```

---

## 🧠 How it works

1. **Flask (`app.py`)** serves `templates/index.html` on `/`, and exposes a
   JSON endpoint at `/api/news` that the frontend calls with query
   parameters (`section`, `q`, `category`, `date`, `source`, `limit`,
   `refresh`).
2. **`api.py`** is the only file that talks to MediaStack. Your API key
   stays on the server -- it is never sent to the browser.
3. **`static/js/script.js`** is plain JavaScript that calls `/api/news`
   with `fetch()`, renders the JSON response into cards using a
   `<template>` element, and manages search, filters, refresh, and
   bookmarking (via `localStorage`, so saved articles survive a page
   reload, unlike a purely in-memory session).
4. A tiny in-memory cache (5 minutes TTL) on the Flask side avoids
   hammering MediaStack every time you switch sidebar tabs; the Refresh
   button sends `refresh=1` to bypass it.

---

## ☁️ Deploying to Vercel

This project includes a Vercel-ready structure:

```
TradingNewsDashboardVercel/
│── api/
│   └── index.py           # Vercel entry point -- imports the Flask app from app.py
│── app.py                 # Same Flask app as local dev, unchanged
│── mediastack.py            # MediaStack API wrapper (renamed from api.py to avoid
│                              # clashing with the required api/ folder)
│── utils.py
│── templates/index.html
│── static/css/style.css
│── static/js/script.js
│── requirements.txt
│── vercel.json              # Routes all traffic to api/index.py, static/ served directly
│── .vercelignore             # Keeps .env and __pycache__ out of the deployment
└── .env                       # LOCAL DEV ONLY -- see below for production
```

1. Install the CLI: `npm install -g vercel`
2. From this folder, run `vercel login`, then `vercel` (or `vercel --prod`).
3. Add your API key as an environment variable (NOT via `.env`, which is
   excluded from the deployment):
   ```bash
   vercel env add MEDIASTACK_API_KEY
   ```
   or via the Vercel dashboard: Project → Settings → Environment Variables.
4. Redeploy with `vercel --prod` so the new environment variable takes effect.

---

## 🛠️ Setup

### 1. Enter the project folder
```bash
cd TradingNewsDashboardHTML
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get a free MediaStack API key
1. Sign up at [https://mediastack.com/](https://mediastack.com/).
2. Copy your API access key from the dashboard.
3. Open `.env` in the project root and paste your key:

```env
MEDIASTACK_API_KEY=your_actual_key_here
```

> ⚠️ Never commit your real `.env` file to a public repository.
> On the free MediaStack plan, requests are made over **HTTP** (not HTTPS)
> -- this is a MediaStack platform limitation, not a bug in this app.

### 5. Run the app
```bash
python app.py
```

Open your browser to `http://localhost:5000`.

---

## 🔍 How Search & Categories Work

MediaStack's built-in categories are limited to: `general`, `business`,
`entertainment`, `health`, `science`, `sports`, `technology`. It does not
have finance-specific categories like "Banking" or "Auto Sector", so this
dashboard maps each sidebar section to a **targeted keyword search**
(defined in `utils.py -> SECTION_CONFIG`) that best represents that topic.
Typing your own search query always overrides the current section's
default keywords, and the Category filter dropdown can further narrow
results to one of MediaStack's real categories.

---

## 🧩 Tech Stack

| Layer            | Technology                     |
|-------------------|---------------------------------|
| Backend framework | Flask (Python)                  |
| HTTP requests     | requests                        |
| Env variables     | python-dotenv                   |
| Data handling     | pandas                          |
| Frontend          | Plain HTML5 + CSS3 + vanilla JS |
| Persistence       | Browser `localStorage` (saved articles only) |

No React, Vue, Angular, Next.js, or Node.js is used anywhere in this project.

---

## ⚠️ Notes for a College Project

- All code is modular and commented for readability.
- No placeholder/fake data is used anywhere -- every article shown comes
  from a live MediaStack API response.
- The MediaStack API key is only ever used server-side inside `api.py`.
- Saved articles live in the browser's `localStorage`, so they're specific
  to one browser/device and reset if the user clears their browser data.

---

## 📄 License

This project is provided for educational purposes.
