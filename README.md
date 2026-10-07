# DemaciAI

A personal study tool for one League of Legends player: given an enemy champion and lane, it shows how to
play Garen in that matchup (runes, build, every phase of the lane), built from what high-elo Garen players and
the community say, with a source link, date and freshness note on every tip.

This repository holds the code only. The collected source text and notes stay private on the author's computer.

## What's here

- `scripts/`: Python pipeline. Polite, cached fetching of public sources (Riot Data Dragon, the League of
  Legends wiki's patch history, YouTube transcripts, guide pages, rank-filtered stats), a kit-change log that
  decides whether a tip is still valid, and the steps that turn sourced claims into matchup pages.
- `frontend/`: the web app (Vite, React, TypeScript, Tailwind, Motion, GSAP) that displays the matchup pages.
  It only reads exported JSON and locally cached Data Dragon art.
- `config.yaml`: sources, weights and rules.

## Reddit API use (`scripts/fetch_reddit.py`)

Planned, and switched off in `config.yaml` until Reddit approves API access.

- **Read-only, app-only OAuth** (client credentials, script app). It never posts, comments, votes or messages.
- **What it reads:** posts and top comments in r/Garenmains (and possibly r/summonerschool,
  r/leagueoflegends) that discuss Garen against a specific champion.
- **Volume:** a few hundred requests per month at most. Requests are at least 2 seconds apart and cached
  locally, so nothing is fetched twice.
- **What happens to the data:** short summaries of the advice are saved, each with the thread link, author and
  date, as private notes on the author's computer. The summaries are written with help from an AI assistant;
  Reddit content is not used to train any model, and nothing is published, shared or sold.

## Running it

```
pip install -r requirements.txt
copy .env.example .env        # fill in your own credentials
cd frontend && npm install && npm run dev
```

The app needs exported data (`scripts/export_frontend.py`) and cached art (`scripts/fetch_frontend_assets.py`),
which are not included here.

Garen Companion isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone
officially involved in producing or managing Riot Games properties. Riot Games and all associated properties
are trademarks or registered trademarks of Riot Games, Inc.
