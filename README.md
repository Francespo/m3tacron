# M3tacron

A centralized meta-aggregator for X-Wing Miniatures Game competitive data.

**[Live Demo (Placeholder)](https://your-reflex-deploy-url.com)**

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

This project showcases a modern, Python-first architecture, designed to handle complex data aggregation while serving a reactive frontend from a unified codebase.

### Architecture Highlights
- **Full-Stack Reflex**: Built entirely with [Reflex](https://reflex.dev/). This eliminates the traditional Javascript/Python context switch, allowing rich UI components (React under the hood) to be written and managed purely in Python.
- **Advanced Scraping with Playwright**: Features an object-oriented ingestion pipeline. It leverages **Playwright** for robust, browser-based scraping to handle dynamic JavaScript-rendered content, standardizing disparate data structures from third-party platforms (Longshanks, Rollbetter, Listfortress) into a unified internal model.
- **Event-Driven State**: Leverages Reflex's `State` system for sophisticated, real-time client interactions—managing global filters, cross-component communication, and dynamic data pagination without heavy page reloads.
- **Data Layer (SQLite & Supabase)**: Powered by SQLite (via SQLModel/SQLAlchemy integration) for rapid, lightweight local development and testing, with a streamlined migration path to **Supabase** (PostgreSQL) for scalable, high-performance production deployments.

### Running it locally

1. **Clone the repo**:
   ```bash
   git clone https://github.com/yourusername/m3tacron.git
   cd m3tacron
   ```
2. **Set up a virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # source .venv/bin/activate on macOS/Linux
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment setup (The Local Database)**:
   The repository includes a `test.db` SQLite database so you can preview the app immediately without needing to scrape data or set up PostgreSQL.
   Create a `.env` file in the root directory and add:
   ```env
   DATABASE_URL="sqlite:///test.db"
   ```
   *(Note: backend scripts and `reflex run` will automatically default to `test.db` if `DATABASE_URL` is omitted, but creating an `.env` is recommended for running local scraper scripts safely).*
5. **Start the app**:
   ```bash
   reflex run
   ```

---

## Disclaimer

**M3tacron** is an unofficial fan project and is not endorsed by, sponsored by, or affiliated with Lucasfilm Ltd., Disney, Fantasy Flight Games, or Atomic Mass Games. 

All Star Wars characters, names, images, and related content are trademarks and/or copyrights of their respective property owners. The data aggregated by this tool is strictly for informational and non-commercial purposes.
