# M3tacron

A centralized meta-aggregator for X-Wing Miniatures Game competitive data.

<details open>
<summary><strong>Table of Contents</strong></summary>

- [Features](#features)
- [Under the Hood & Setup](#under-the-hood--setup)
- [Disclaimer](#disclaimer)

</details>

---

## Features

M3tacron brings together competitive data from different platforms so you don't have to check multiple websites.

- **Data Aggregation**: Pulls tournament results from Longshanks, Rollbetter, and Listfortress.
- **Search & Filter**: Find tournaments, lists, and pilots using global filters.
- **Analytics**: Browse top-performing lists to see what's currently working in the meta.
- **Responsive UI**: Works seamlessly on both desktop and mobile screens.

---

## Under the Hood & Setup

### Architecture

M3tacron uses a decoupled architecture with two independent layers:

- **Frontend** — [SvelteKit](https://svelte.dev/docs/kit) + [Tailwind CSS v4](https://tailwindcss.com/) + [Chart.js](https://www.chartjs.org/). A fast, server-rendered UI with client-side navigation and reactive data fetching.
- **Backend** — [FastAPI](https://fastapi.tiangolo.com/) (Python). A RESTful API serving tournament data, analytics, and meta snapshots.
- **Scraping** — An object-oriented ingestion pipeline leveraging **Playwright** for robust, browser-based scraping of dynamic JavaScript-rendered content from Longshanks, Rollbetter, and Listfortress.
- **Data Layer** — SQLite (via SQLModel/SQLAlchemy) for local development, with a migration path to **Supabase** (PostgreSQL) for production.

### Running it locally

1. **Clone the repo**:
   ```bash
   git clone https://github.com/Francespo/m3tacron.git
   cd m3tacron
   ```

2. **Set up the Python backend**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

3. **Prepare the local database**:
   The repository includes a `seed.db` with demo data. Copy it so you can preview the app immediately:
   ```bash
   cp seed.db test.db
   ```
   Then create a `.env` file in the root directory:
   ```env
   DATABASE_URL="sqlite:///test.db"
   ```

4. **Install frontend dependencies**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Start both servers**:

   **Terminal 1 — Backend** (from project root):
   ```bash
   python -m uvicorn backend.main:app --reload --port 8100
   ```

   **Terminal 2 — Frontend** (from `frontend/`):
   ```bash
   cd frontend
   npm run dev
   ```

   The site will be available at `http://localhost:5173`, with the API at `http://localhost:8100`.

---

## Disclaimer

**M3tacron** is an unofficial fan project and is not endorsed by, sponsored by, or affiliated with Lucasfilm Ltd., Disney, Fantasy Flight Games, or Atomic Mass Games.

All Star Wars characters, names, images, and related content are trademarks and/or copyrights of their respective property owners. The data aggregated by this tool is strictly for informational and non-commercial purposes.
