# Global Tech Pulse

A responsive Thai-language technology news dashboard for GitHub Pages, with an automated RSS aggregation pipeline.

## Features
- Global tech news from 9 RSS feeds, with direct source links and publication timestamps.
- AI, Big Tech, Cybersecurity, Startups, Chips and Policy filters.
- Search, sort, more stories, and mobile-friendly design.
- Eight technology leaders with Google News tracking links and in-feed mention counts.
- GitHub Actions workflow that refreshes `data/news.json` every 3 hours (scheduled workflows may be delayed).
- Client-only web application: no API keys or backend hosting needed.

## Deploy
1. Create a public GitHub repository named `global-tech-pulse`.
2. Upload all files preserving `.github/workflows/update-news.yml`.
3. Under **Settings → Pages**, choose **Deploy from a branch**, `main`, `/ (root)` and save.
4. Under **Actions → Update technology news → Run workflow**, trigger the first fetch. The news feed starts empty until a successful run.
5. Visit `https://YOUR_USERNAME.github.io/global-tech-pulse/`.

Ensure **Settings → Actions → General → Workflow permissions** permits read/write access for GitHub Actions (or configure the repository's workflow token accordingly). Scheduled runs are best-effort and not guaranteed to happen at exactly the same minute.

## Run locally

```bash
python scripts/update_news.py
python -m http.server 8000
```

Browse to `http://localhost:8000/`. The RSS script uses Python standard library only.

## Editorial notes
News titles and short snippets are attributed and link to original publishers. Article categories are simple keyword-based labels and may occasionally be imperfect. Leader counts are mentions in collected articles, not a comprehensive social-media feed or validation of current titles. Check original sources for accuracy.
