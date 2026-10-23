# PDX IRL

**Portland is better offline.**

A fast, funky, mobile-first Portland event discovery PWA built to answer one question: **what cool shit is happening?**

## v0.3.1.1 — Real Event Engine + iPhone polish

- Today / Tonight / Weekend / Upcoming
- Multi-category filtering, search, and 21+ filter
- Want to Go + Attended saved locally
- Calendar export (.ics)
- Surprise Me
- iPhone safe areas, sticky mobile navigation, touch-sized controls
- Installable PWA icons + standalone mode
- Scheduled GitHub Actions event refresh
- Source-specific collectors for Travel Portland and broader Portland calendars, with JSON-LD fallback for venues
- Normalization, multi-category tagging, 21+ detection, and deduplication
- Source-by-source counts in Actions logs

## Event refresh

`.github/workflows/refresh-events.yml` runs the collector daily and Thursday afternoon. You can also run **Refresh Portland events** manually from GitHub Actions.

The event engine is intentionally adapter-based. Websites change. A source failing should not take down the rest of the feed; its failure is reported in `data/meta.json` and the Actions log.

## Install on iPhone

Open the GitHub Pages site in Safari → Share → **Add to Home Screen**. PDX IRL launches in standalone mode.
