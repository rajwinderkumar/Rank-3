# Rank Wise

Web-based **on-page SEO performance analysis** tool.

Paste a public URL. Rank Wise fetches the page and checks:

1. Page title  
2. Meta description  
3. Headings (H1 / H2 / H3)  
4. Image alt text  
5. Internal / external links  
6. URL structure  
7. robots.txt  
8. sitemap.xml  

You get a **0–100 score**, plain-language recommendations, and a saved history.

**Stack (as in the project synopsis):** HTML, CSS, JavaScript, Python, Flask.

---

## Project structure

```
rank-wise/
├── index.html          # Home / audit form
├── history.html        # Saved audits
├── favicon.svg
├── css/
│   └── rankwise.css
├── js/
│   └── rankwise.js
├── backend/
│   ├── app.py          # Flask API
│   ├── requirements.txt
│   └── seo/
│       ├── __init__.py
│       └── run_audit.py
├── .gitignore
└── README.md
```

---

## Run locally

### 1. Backend (required for live URL audits)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

API runs at **http://127.0.0.1:5000**

### 2. Frontend

Open `index.html` in a browser, **or** serve the folder:

```bash
# from rank-wise/
python -m http.server 8080
```

Then open **http://127.0.0.1:8080**

If the API is on another host, set it before loading the script:

```html
<script>window.RANK_WISE_API = "https://your-api.onrender.com";</script>
```

**Sample report** works without the backend (uses built-in sample data).

---

## Host on GitHub

### Option A — GitHub Pages (frontend only)

1. Create a new GitHub repository (e.g. `rank-wise`).
2. Upload this whole folder (or push with git).
3. **Settings → Pages → Source:** deploy from branch `main` / root (or `/docs` if you move files there).
4. Site URL will look like: `https://YOUR_USER.github.io/rank-wise/`

Live URL audits still need the Flask API. Set `RANK_WISE_API` in both HTML files to your deployed backend URL.

### Option B — Full stack with Flask serving static files

On a VPS or [Render](https://render.com):

1. Root directory: `backend`
2. Build: `pip install -r requirements.txt`
3. Start: `gunicorn app:app`
4. Flask already serves `index.html`, CSS, and JS from the parent folder.

Environment variable: `PORT` (Render sets this automatically).

### Option C — Git + local

```bash
cd rank-wise
git init
git add .
git commit -m "Initial Rank Wise project"
git branch -M main
git remote add origin https://github.com/YOUR_USER/rank-wise.git
git push -u origin main
```

---

## API

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/health` | — | Health check |
| POST | `/api/audit` | `{ "url": "https://example.com" }` | Run SEO audit |
| GET | `/api/audit/<id>` | — | Get one saved audit |
| GET | `/api/history` | — | List recent audits |

History is also stored in the browser (`localStorage`) so the History page works even if the API is offline.

---

## Notes

- Only **public** http/https pages are audited. Localhost and private IPs are blocked.
- The score is an assessment of the eight checks above. It is **not** a search ranking prediction.
- Technologies match the synopsis: HTML, CSS, JS, Python, Flask. Optional Supabase can replace the JSON file store later if you want a shared cloud database.
