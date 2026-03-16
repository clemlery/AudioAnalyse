# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (uses uv)
pip install -e .

# Run Streamlit web UI
streamlit run 1_home.py

# Run CLI entry point
python main.py

# Run database migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"
```

There is no test suite. Validation happens through logging (`./log/exploit_streaming_history.log`).

## Architecture

The app ingests Spotify streaming history JSON exports, enriches the data via the Spotify API and web scraping, persists everything to PostgreSQL, and exposes it through a Streamlit UI.

**Data flow:**
```
JSON files (data/uploads/) → ingest.py → process.py → PostgreSQL → Streamlit pages
```

**Layer structure:**

- **UI** (`1_home.py`, `pages/`) — Streamlit multi-page app
- **Services** (`streaming_history_analyser/`) — ingestion pipeline, reporting, visualization
  - `ingest.py`: entry point, reads JSON files matching `Streaming_History_Audio_*.json`
  - `process.py`: core enrichment algorithm (filter new IDs → fetch API → scrape → persist)
  - `factory.py`: `ScraperFactory` and `TokenSource` protocol for dependency injection
- **DAOs** (`dao/`) — three sub-layers:
  - `db_dao/`: SQLAlchemy CRUD for all entities
  - `fetch_dao/`: Spotify API v1 clients (tracks, artists, albums, user)
  - `scrap_dao/`: Selenium browser scraping for monthly listeners and playcounts
- **Models** (`models/`) — two sub-layers:
  - `sql_alchemy_models/`: ORM table definitions
  - `data_class_models/`: Pydantic models for Spotify API responses
- **Config** (`config.py`): SQLAlchemy engine and session; `auth.py`: Spotify OAuth

## Database

PostgreSQL database named `lyra`. Key tables: `artist`, `track`, `release`, `spotify_track` (track on a specific release), `track_stream` (per-user aggregate), `track_stream_day` (daily aggregate), `artist_metrics_snapshot`, `track_metrics_snapshot`. Many-to-many associations: `track_artist`, `release_artist`.

Schema is managed by Alembic. Always run `alembic upgrade head` after pulling changes that include new migration files.

## Environment

Requires a `.env` file with:
- `CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI` — Spotify OAuth app credentials
- `UID`, `PASSWORD`, `SERVER`, `DATABASE` — PostgreSQL connection
- `SECRET_KEY`, `BASE_URL` — Streamlit session config

Key constants (paths, enums, batch sizes) are in `constants/service.py`. `USER_ID` is hardcoded there as the Spotify user ID for DB lookups.

## Key Patterns

- **Factory pattern**: `ScraperFactory` in `factory.py` instantiates DAO objects; use it for DI instead of constructing DAOs directly.
- **Batch processing**: `BATCH_SIZE=200` controls API call chunking in `process.py`.
- **Token extraction**: The scraper obtains Spotify auth tokens by intercepting CDP network logs via `dao/service.py:BrowserManager`.
- **Logging**: Rotating file logs at `./log/exploit_streaming_history.log`; configured in `config.py`.
