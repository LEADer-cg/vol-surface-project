
# Volatility Surface Project

This repository contains an end-to-end prototype for fetching option chains,
computing implied volatility (via Black–Scholes inversion), constructing
an implied volatility surface, persisting snapshots into a PostgreSQL database,
and visualizing using Streamlit.

## Quick start (development)

1. Copy `.env.example` to `.env` and adjust if needed.
2. Build and run with docker-compose:
```bash
docker-compose up --build
```
3. Open Streamlit UI at http://localhost:8501

## Contents
- `volcalc/` - core calculation modules (Black–Scholes, fetcher, surface builder, DB, snapshotter)
- `app/streamlit_app.py` - Streamlit UI
- `tests/` - simple unit tests
- `Dockerfile`, `docker-compose.yml` - for containerized run
