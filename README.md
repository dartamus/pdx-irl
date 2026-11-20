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

## v0.5 collector engine (November 2026)

This release adds a two-stage discovery process: inspect source listings for plausible event-detail URLs, fetch a bounded set of those pages, and extract events only when a real start date is present. Singles and Social are distinct categories; a source's identity alone does not make every listing a singles event. Existing event/ticket URL behavior is retained.

**New sources:** Eventbrite singles and speed dating, Meetup singles discovery, FunPDX meet-people, Helium Comedy, Portland Art Museum, and Portland'5, in addition to the existing sources. These are *candidate integrations*, not a guarantee that every site permits scraping or publishes machine-readable events. Some may block GitHub Actions or require an official API. A source is working only when the GitHub Action reports a nonzero valid event count.

**Run local tests:** `python -m unittest discover -s tests -v` after `pip install -r scripts/requirements.txt`. Run the collector with `python scripts/refresh_events.py` from the repository root (requires outbound internet). `data/meta.json` includes `candidatePages`, `pagesChecked`, `rejectedNoDirectLink`, `found`, and source errors. Zero-result sources are highlighted in workflow logs. This release has fixture-based parser tests; it was not possible to run a live internet collection in the build environment.

**Deployment:** Upload the contents of this ZIP to the root of the GitHub repository. Unlike prior releases, **update `.github/workflows/refresh-events.yml`** as well to enable the collector tests. The new `scripts/collectors_v05.py` and `tests/test_collectors.py` must be committed. Do not upload `__pycache__` or `.bak` files.

## v0.6 design update (Nov 2026)

The homepage is now a minimal punk-zine discovery flow: **When → What → Go**. Time choices: Tonight, This Weekend, Tomorrow, Plan Ahead. Category rows have restrained category colors (music blue, comedy pink, singles red). Choose a category or Show Me Everything to open the event feed. Surprise Me chooses from matching events. Saved and filters remain available in the mobile navigation. No emoji UI. Existing collectors, GitHub Actions, event JSON, PWA and `.ics` calendar download are retained.

Deploy by uploading the contents of the `pdx-irl-main` folder to the root of the GitHub repository, replacing existing files. Keep `.github/workflows/refresh-events.yml` and `tests/` intact. The service worker cache key was bumped to `pdx-irl-v06`.


## v0.6.1 visual refinement
Retains the PDX IRL logo and When → What → Go interaction, but uses a compact editorial homepage, restrained category accents, quieter event cards, and reduced visual noise. No collector changes.
