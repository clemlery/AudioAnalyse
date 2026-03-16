# Spotify Streaming History Analyser

A Python app to ingest your extended Spotify streaming history, enrich it with data from the Spotify API and web scraping, store everything in PostgreSQL, and explore it through an interactive Streamlit dashboard.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [License](#license)

## Overview

Spotify lets you export your full streaming history as a set of JSON files. This project takes those files, enriches each track with metadata fetched from the Spotify API (album, artists, popularity…) and scraped from the web (monthly listeners, playcounts), and persists it all in a local PostgreSQL database. You can then explore your listening habits through a multi-page Streamlit web UI.

## Features

- **Data ingestion** — batch-process `Streaming_History_Audio_*.json` files
- **API enrichment** — fetch track, artist, and album metadata from the Spotify Web API
- **Web scraping** — collect monthly listeners and playcounts via Selenium
- **PostgreSQL persistence** — full relational model with migrations via Alembic
- **Daily aggregates** — per-track stream counts, skip counts, and play durations rolled up by day
- **Historical snapshots** — track how artist monthly listeners and track playcounts evolve over time
- **Streamlit dashboard** — multi-page UI to browse top artists/tracks/releases and custom scoring metrics
- **CSV exports** — export summary tables for use outside the app

## Tech Stack

| Layer | Library |
|---|---|
| Web UI | Streamlit |
| Data analysis | Pandas, Matplotlib |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Database | PostgreSQL |
| API client | Requests (Spotify Web API) |
| Scraping | Selenium, Playwright |
| Validation | Pydantic |
| Runtime | Python 3.12, uv |

## Prerequisites

- Python 3.12+
- PostgreSQL server (local)
- A [Spotify Developer app](https://developer.spotify.com/dashboard) (Client ID + Secret)
- Chrome/Chromium (for Selenium scraping)

## Installation & Setup

1. **Clone the repo**

   ```bash
   git clone <repo-url>
   cd VibeCoding-AudioAnalyse
   ```

2. **Install dependencies** (using [uv](https://github.com/astral-sh/uv))

   ```bash
   pip install -e .
   ```

3. **Create a `.env` file** at the project root:

   ```env
   # Spotify OAuth
   CLIENT_ID=your_spotify_client_id
   CLIENT_SECRET=your_spotify_client_secret
   REDIRECT_URI=http://localhost:8501/callback

   # Streamlit
   BASE_URL=http://localhost:8501
   SECRET_KEY=some_random_secret

   # PostgreSQL
   UID=your_db_user
   PASSWORD=your_db_password
   SERVER=localhost
   DATABASE=lyra
   ```

4. **Create the database** and run migrations:

   ```bash
   createdb lyra
   alembic upgrade head
   ```

## Usage

### Web UI (recommended)

```bash
streamlit run 1_home.py
```

Then open `http://localhost:8501`. The app guides you through:

1. **Import** — authenticate with Spotify and upload your JSON export files
2. **Top items** — browse your most-listened artists, tracks, and releases
3. **Custom values** — explore Interest Score and Commitment Ratio metrics

### CLI

```bash
python main.py
```

Currently runs the streaming history visualization pipeline directly.

## How It Works

```
JSON exports (data/uploads/)
        │
        ▼
ingest.py — reads and validates files
        │
        ▼
process.py — for each new track:
  ├─ fetch metadata from Spotify API  (dao/fetch_dao/)
  ├─ scrape monthly listeners & playcounts  (dao/scrap_dao/)
  ├─ persist artists, releases, tracks  (dao/db_dao/)
  └─ record stream events and daily aggregates
        │
        ▼
reporting.py — export CSV summaries (data/csv/)
        │
        ▼
visualize.py / Streamlit pages — charts and analysis
```

The scraper obtains a valid Spotify auth token by intercepting CDP network logs from a headless Chrome session managed by `dao/service.py:BrowserManager`.

## Project Structure

```
.
├── 1_home.py                        # Streamlit entry point
├── main.py                          # CLI entry point
├── config.py                        # DB engine, session, logging
├── auth.py                          # Spotify OAuth helpers
├── constants/                       # API endpoints, paths, enums
├── models/
│   ├── data_class_models/           # Pydantic models for API responses
│   └── sql_alchemy_models/          # ORM table definitions
├── dao/
│   ├── db_dao/                      # PostgreSQL CRUD operations
│   ├── fetch_dao/                   # Spotify API clients
│   └── scrap_dao/                   # Selenium-based scrapers
├── streaming_history_analyser/
│   ├── ingest.py                    # File loading & orchestration
│   ├── process.py                   # Core enrichment pipeline
│   ├── factory.py                   # ScraperFactory (dependency injection)
│   ├── reporting.py                 # CSV export
│   └── visualize.py                 # Matplotlib charts
├── pages/                           # Streamlit sub-pages
├── alembic/                         # DB migration scripts
├── data/
│   ├── uploads/                     # Drop your JSON exports here
│   └── csv/                         # Generated CSV reports
└── log/                             # Rotating application logs
```

## License

MIT
