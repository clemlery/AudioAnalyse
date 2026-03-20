# Lyra — Spotify Listening Analytics & Recommendations

A multi-user platform that ingests Spotify extended streaming history, enriches it with metadata from the Spotify API and web scraping, and turns raw play counts into personalized music recommendations through an interactive Streamlit dashboard.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Set Up](#set-up)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [License](#license)

## Overview

Spotify lets you export your full listening history as a set of JSON files. Lyra takes those files, enriches every track with metadata from the Spotify Web API (album, artists, popularity, audio features) and from web scraping (monthly listeners, global playcounts), and stores the result in a structured PostgreSQL database.

From there, each authenticated user gets a personal analytics dashboard — top artists, top tracks, listening trends over time, and custom engagement metrics (Interest Score, Commitment Ratio). Because the data is shared across users, Lyra can also identify listeners with similar taste profiles and use that signal to surface music you're likely to enjoy but haven't discovered yet.

The goal is simple: own your listening data, understand your habits deeply, and get recommendations that are actually grounded in what you listen to — not a black-box algorithm.

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

## Set Up

### 1. Prerequisites

Make sure the following are installed on your machine before starting.

#### Python 3.12+ and uv

[uv](https://github.com/astral-sh/uv) is used as the package manager.

```bash
# Install uv (Linux/macOS)
curl -Ls https://astral.sh/uv/install.sh | sh

# Verify
uv --version
python3 --version  # must be 3.12+
```

```powershell
# Install uv (Windows — PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify
uv --version
python --version  # must be 3.12+
```

> On Windows, Python 3.12+ can also be installed from [python.org](https://www.python.org/downloads/) or via `winget install Python.Python.3.12`. Make sure to check **"Add Python to PATH"** during installation.

#### PostgreSQL

```bash
# Ubuntu / Debian
sudo apt install postgresql postgresql-contrib

# macOS (Homebrew)
brew install postgresql
brew services start postgresql

# Fedora / RHEL
sudo dnf install postgresql postgresql-server
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

```powershell
# Windows — using winget
winget install PostgreSQL.PostgreSQL

# Or download the installer from https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
# During installation, note the password you set for the 'postgres' superuser.
```

After installation, create a dedicated database user (or use an existing one):

```bash
# Linux / macOS
sudo -u postgres psql
```

```powershell
# Windows — open a new PowerShell and run:
psql -U postgres
```

```sql
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
ALTER USER your_db_user CREATEDB;
\q
```

> On Windows, PostgreSQL tools (`psql`, `createdb`) are installed under `C:\Program Files\PostgreSQL\<version>\bin`. Add this directory to your `PATH` environment variable so the commands are available in your terminal.

#### Google Chrome + ChromeDriver

Selenium requires a Chrome browser and a matching ChromeDriver. Install Chrome from the [official site](https://www.google.com/chrome/), then install ChromeDriver:

```bash
# Ubuntu / Debian
sudo apt install chromium-driver

# macOS (Homebrew)
brew install --cask chromedriver

# Or use the selenium-manager bundled with Selenium 4.6+ (automatic)
```

```powershell
# Windows — install Google Chrome from https://www.google.com/chrome/
# ChromeDriver is handled automatically by Selenium 4.6+ via selenium-manager.
# No manual install needed in most cases.
```

> Selenium 4.6+ ships with `selenium-manager` which can download ChromeDriver automatically. If it works on your machine, no manual install is needed.

---

### 2. Spotify Developer App

The app uses the Spotify Web API for metadata enrichment and OAuth authentication.

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in.
2. Click **Create app**.
3. Fill in a name and description (anything works).
4. Set the **Redirect URI** to: `http://localhost:8501/callback`
5. Select **Web API** as the API to use.
6. Save and open the app settings — copy the **Client ID** and **Client Secret**.

---

### 3. Clone and install

```bash
git clone <repo-url>
cd VibeCoding-AudioAnalyse

# Install all dependencies in a virtual environment
pip install -e .
```

> If you prefer using uv directly: `uv pip install -e .`

---

### 4. Environment variables

Create a `.env` file at the project root with the following content:

```env
# Spotify OAuth — from your Developer Dashboard
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=http://localhost:8501/callback

# Streamlit session
BASE_URL=http://localhost:8501
SECRET_KEY=some_random_secret_string

# PostgreSQL connection
UID=your_db_user
PASSWORD=your_db_password
SERVER=localhost
DATABASE=lyra
```

| Variable | Description |
|---|---|
| `CLIENT_ID` | Spotify app client ID |
| `CLIENT_SECRET` | Spotify app client secret |
| `REDIRECT_URI` | Must match exactly what you set in the Spotify dashboard |
| `BASE_URL` | Base URL of the Streamlit server |
| `SECRET_KEY` | Arbitrary secret used for session signing |
| `UID` | PostgreSQL user |
| `PASSWORD` | PostgreSQL user password |
| `SERVER` | PostgreSQL host (usually `localhost`) |
| `DATABASE` | PostgreSQL database name (default: `lyra`) |

---

### 5. Database setup

Create the database and apply all schema migrations:

```bash
# Create the database
createdb lyra
# or with explicit user:
createdb -U your_db_user lyra

# Apply all Alembic migrations
alembic upgrade head
```

To verify the schema was created correctly:

```bash
psql -U your_db_user -d lyra -c "\dt"
```

You should see the tables: `artist`, `track`, `release`, `spotify_track`, `user`, `track_stream`, `track_stream_day`, `track_metrics_snapshot`, `artist_metrics_snapshot`.

> After pulling future changes that include new migration files, always re-run `alembic upgrade head` to apply them.

---

### 6. Folder structure check

Make sure the following directories exist (they are in `.gitignore` but required at runtime):

```bash
# Linux / macOS
mkdir -p data/uploads data/csv log
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path data/uploads, data/csv, log
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
