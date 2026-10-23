# PDX IRL

**Portland is better offline.**

A fast, funky Portland event discovery app built to answer one question: **what cool shit is happening?**

## v0.1
- Today / Tonight / Weekend / Upcoming
- Category, search, and 21+ filters
- Want to Go + Attended stored locally
- Add-to-calendar (.ics)
- Surprise Me
- Installable PWA foundation
- Event data separated into `data/events.json`

## Run locally
Because the app fetches JSON, serve the folder instead of double-clicking `index.html`:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## GitHub Pages
Settings → Pages → Deploy from a branch → `main` → `/ (root)`.

## Next
Automated multi-source event ingestion, normalization, deduplication, richer filters, calendar connection, and personalized recommendations.
