# UrlShortener ⚡

A fast, minimal URL shortener built with Python and Flask, deployed on Railway.

## What it does

Paste a long URL → get a short link → share it anywhere. Tracks click counts for every link.

## Tech stack

- **Flask** — Python web framework
- **PostgreSQL** — database (hosted on Railway)
- **Railway** — deployment and hosting

## Run locally
```bash
git clone https://github.com/SavithOnline/UrlShortener
cd UrlShortener
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:
```
DATABASE_URL=your_postgres_url_here
SECRET_KEY=any-random-string
```

Then run:
```bash
python app.py
```

Visit `http://localhost:5000`

## Deploy

This app auto-deploys to Railway on every `git push` to `main`.

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask session secret |