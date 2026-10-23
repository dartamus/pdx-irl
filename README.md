# PDX IRL

**Portland is better offline.**

A fast, funky Portland event discovery app built to answer one question: **what cool shit is happening?**

## v0.2 — Content Engine

- Today / Tonight / Weekend / Upcoming
- Multi-category filtering, search, and 21+ filter
- Want to Go + Attended stored locally
- Calendar export
- Surprise Me
- 20+ current seed events while the automated engine ramps up
- Automated event ingestion from Portland event/venue pages using JSON-LD
- Normalization + deduplication
- Daily refresh plus a Thursday Weekend Drop refresh via GitHub Actions
- `data/meta.json` freshness/status metadata

## How event refresh works

`.github/workflows/refresh-events.yml` runs `scripts/refresh_events.py`. The script checks every page in `scripts/sources.json`, extracts structured Event data, normalizes categories and 21+ signals, deduplicates records, and updates `data/events.json`.

To add another source, add its calendar URL to `scripts/sources.json`. Pages that publish schema.org Event / JSON-LD work best.

You can also run the refresh manually from **GitHub → Actions → Refresh Portland events → Run workflow**.

## GitHub Pages

Serve from `main` / root.
