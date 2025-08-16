# Spotify Streaming Data Analyzer

A Python tool to ingest an extended Spotify streaming history, persist it in a PostgreSQL database, and generate CSV reports and visualizations.

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Tech Stack](#tech-stack)
* [Prerequisites](#prerequisites)
* [Installation & Setup](#installation--setup)
* [Usage](#usage)
* [Project Structure](#project-structure)
* [How It Works](#how-it-works)
* [Generating Reports & Charts](#generating-reports--charts)
* [License](#license)

## Overview

This project automates the ingestion of a user’s extended Spotify streaming history (exported as JSON), stores both the stream events and all related metadata (artists, releases, tracks) in a PostgreSQL database, and then produces CSV exports and statistical visualizations using Pandas and Matplotlib.

## Features

* **Data Ingestion**

  * Load JSON files from an `uploads/` folder
  * Cache Spotify IDs in memory to minimize redundant DB queries
  * Persist stream events to a `Track_Stream` table
  * Auto-create or update related metadata tables: `Artist`, `Release`, `Spotify_Track`, `Track`

* **Database-Backed**

  * SQLAlchemy ORM for DAO definitions and CRUD
  * Alembic for schema migrations

* **Reporting & Visualization**

  * SQL queries with joins to extract summary tables
  * Export `artists.csv`, `tracks.csv`, and `releases.csv`
  * Load CSVs into Pandas DataFrames
  * Generate bar charts and scatter plots with Matplotlib

## Tech Stack

* **Python** 3.12
* **Pydantic** — data validation & classes
* **SQLAlchemy** — ORM & database operations
* **PostgreSQL** — local development database
* **Alembic** — migrations
* **csv**, **pandas**, **matplotlib** — CSV export, data analysis, and plotting

## Prerequisites

* Python 3.7+
* PostgreSQL server (local)
* `virtualenv` or `venv` (recommended)

## Installation & Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/your-username/spotify-stream-analyzer.git
   cd spotify-stream-analyzer
   ```

2. **Create & activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux / macOS
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**

   * Create a PostgreSQL database (e.g. `spotify_history`)
   * Set your DB URL in `alembic.ini` and/or environment variable, e.g.:

     ```bash
     export DATABASE_URL=postgresql://user:password@localhost/spotify_history
     ```

5. **Run migrations**

   ```bash
   alembic upgrade head
   ```

## Usage

1. **Drop your Spotify export JSON files** into the `uploads/` directory.
2. **Run the ingestion & reporting script**:

   ```bash
   python main.py
   ```
3. **Review outputs**:

   * **Database tables** now populated with streaming history and metadata
   * **CSV files** generated under `data/csv/`:

     * `artists.csv`
     * `tracks.csv`
     * `releases.csv`
   * **Charts** will be rendered interactively (or saved if configured)

## Project Structure

```
.
├── alembic
│   ├── env.py
│   └── versions
│       ├── 448246aa6331_update_some_tiny_modifications.py
│       ├── 4a5e71891f8b_change_on_the_field_release_date_table_.py
│       ├── 998030cba0da_creation_of_all_tables.py
│       └── 9987861e6de9_change_on_the_field_name_of_the_table_.py
├── constants
│   ├── api.py
│   └── service.py
├── dao
│   ├── artist_dao.py
│   ├── release_dao.py
│   ├── spotify_track_dao.py
│   ├── track_dao.py
│   ├── track_stream_dao.py
│   └── user_dao.py
├── data
│   ├── font
│   │   └── NotoSansJP-Regular.ttf
│   └── uploads
│       ├── Streaming_History_Audio_2023_0.json
│       ├── Streaming_History_Audio_2023_1.json
│       └── ...
├── database.py
├── graph
│   ├── data_to_csv.py
│   └── graph.py
├── main.py
├── models
│   ├── data_class_models/
│   └── sql_alchemy_models/
├── README.md
└── service.py
```

## How It Works

1. **Ingestion Loop** (in `ingest.py`)

   * Iterate over each JSON file in `uploads/`
   * Load with `json.load()`, yielding a list of Python dicts
   * For each record:

     * If `spotify_id` is in the in-memory cache ⇒ insert only into `Track_Stream`
     * Else:

       1. Check the DB for existing metadata
       2. If missing, insert new `Artist`, `Release`, `Spotify_Track`, `Track` records
       3. Add the ID to the cache
     * Finally insert a `Track_Stream` row

2. **Reporting** (in `reporting.py`)

   * Run SQLAlchemy queries with joins to produce summary tables
   * Write out `artists.csv`, `tracks.csv`, `releases.csv`

3. **Visualization** (in `visualize.py`)

   * Load each CSV into a Pandas DataFrame
   * Create charts (bar plots, scatter plots) using Matplotlib

## Generating Reports & Charts

By default, running `main.py` will:

1. Ingest all JSON files in `uploads/`
2. Migrate the database (if needed)
3. Export CSV summaries to `data/csv/`
4. Open interactive Matplotlib figures for exploration

You can adapt or extend the `visualize.py` module to save figures to disk or tweak styles.

## License

This project is released under the MIT License.
