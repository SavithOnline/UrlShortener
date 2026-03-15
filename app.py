from dotenv import load_dotenv
load_dotenv()

import os
import string
import random
import logging
import psycopg2
import psycopg2.extras
from flask import Flask, request, redirect, render_template_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

def get_db():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id    SERIAL PRIMARY KEY,
            short TEXT UNIQUE NOT NULL,
            long  TEXT NOT NULL,
            hits  INTEGER DEFAULT 0
        )
    """)
    return conn, cur

def make_code():
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=6))

HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>shrtn.ly</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    min-height: 100vh;
    background: #0a0a0a;
    font-family: 'Syne', sans-serif;
    color: #fff;
    padding: 40px 20px;
  }

  .bg-dot {
    position: fixed; inset: 0; pointer-events: none;
    background-image: radial-gradient(circle, #ffffff08 1px, transparent 1px);
    background-size: 24px 24px;
  }

  .accent {
    position: fixed; top: -80px; right: -80px;
    width: 400px; height: 400px; pointer-events: none;
    background: radial-gradient(circle, #6366f125 0%, transparent 70%);
  }

  .wrap { max-width: 560px; margin: 0 auto; position: relative; }

  .logo {
    font-size: 13px; font-weight: 700;
    letter-spacing: 0.15em; color: #ffffff30;
    text-transform: uppercase; margin-bottom: 48px;
  }

  .hero { margin-bottom: 36px; }
  .hero h1 { font-size: 42px; font-weight: 800; line-height: 1.05; margin-bottom: 10px; }
  .hero h1 span { color: #6366f1; }
  .hero p { font-size: 13px; color: #ffffff40; font-family: 'DM Mono', monospace; }

  .input-row { display: flex; gap: 10px; margin-bottom: 14px; }

  .url-input {
    flex: 1; background: #ffffff08; border: 1px solid #ffffff15;
    border-radius: 10px; padding: 14px 18px;
    font-size: 14px; color: #fff; font-family: 'DM Mono', monospace;
    outline: none; transition: border .2s, background .2s;
  }
  .url-input::placeholder { color: #ffffff25; }
  .url-input:focus { border-color: #6366f155; background: #ffffff0d; }

  .btn {
    background: #6366f1; color: #fff; border: none;
    border-radius: 10px; padding: 14px 22px;
    font-size: 14px; font-weight: 700; font-family: 'Syne', sans-serif;
    cursor: pointer; letter-spacing: 0.04em; transition: background .2s, transform .1s;
    white-space: nowrap;
  }
  .btn:hover { background: #4f52d4; }
  .btn:active { transform: scale(0.97); }

  .result-box {
    background: #6366f112; border: 1px solid #6366f135;
    border-radius: 10px; padding: 14px 18px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 36px; animation: fadeIn .3s ease;
  }
  .result-box a { color: #818cf8; font-family: 'DM Mono', monospace; font-size: 14px; text-decoration: none; }
  .result-box a:hover { text-decoration: underline; }

  .copy-btn {
    background: #ffffff10; border: 1px solid #ffffff15; color: #ffffffcc;
    border-radius: 6px; padding: 6px 14px; font-size: 12px;
    cursor: pointer; font-family: 'Syne', sans-serif; transition: background .2s;
  }
  .copy-btn:hover { background: #ffffff18; }

  .error-box {
    background: #ef444412; border: 1px solid #ef444430;
    border-radius: 10px; padding: 14px 18px;
    color: #fca5a5; font-size: 14px; margin-bottom: 36px;
  }

  hr { border: none; border-top: 1px solid #ffffff08; margin-bottom: 28px; }

  .stats-row { display: flex; gap: 12px; margin-bottom: 28px; }
  .stat {
    background: #ffffff06; border: 1px solid #ffffff0d;
    border-radius: 10px; padding: 16px 20px; flex: 1;
  }
  .stat-num { font-size: 28px; font-weight: 800; color: #fff; }
  .stat-label {
    font-size: 11px; color: #ffffff35; text-transform: uppercase;
    letter-spacing: 0.12em; margin-top: 2px; font-family: 'DM Mono', monospace;
  }

  .section-title {
    font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #ffffff25;
    margin-bottom: 12px; font-family: 'DM Mono', monospace;
  }

  .link-row {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 0; border-bottom: 1px solid #ffffff07;
    transition: background .15s;
  }
  .link-row:last-child { border-bottom: none; }

  .short {
    font-family: 'DM Mono', monospace; font-size: 13px;
    color: #818cf8; min-width: 88px; text-decoration: none;
  }
  .short:hover { text-decoration: underline; }

  .arrow { color: #ffffff18; font-size: 12px; }

  .long {
    font-size: 12px; color: #ffffff40; flex: 1;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: 'DM Mono', monospace;
  }

  .hits {
    background: #ffffff08; border-radius: 20px;
    padding: 3px 10px; font-size: 11px; color: #ffffff35;
    white-space: nowrap; font-family: 'DM Mono', monospace;
  }

  .empty { color: #ffffff25; font-size: 14px; text-align: center; padding: 32px 0; }

  @keyframes fadeIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
</style>
</head>
<body>
<div class="bg-dot"></div>
<div class="accent"></div>
<div class="wrap">

  <div class="logo">⚡ shrtn.ly</div>

  <div class="hero">
    <h1>Shorten.<br><span>Share.</span></h1>
    <p>// paste a long url, get a short one</p>
  </div>

  <form method="post">
    <div class="input-row">
      <input class="url-input" type="text" name="url"
             placeholder="https://your-very-long-url-goes-here.com/..."
             required>
      <button class="btn" type="submit">Shorten →</button>
    </div>
  </form>

  {% if short_url %}
  <div class="result-box">
    <a href="{{ short_url }}" target="_blank">{{ short_url }}</a>
    <button class="copy-btn" onclick="navigator.clipboard.writeText('{{ short_url }}');this.textContent='Copied!'">Copy</button>
  </div>
  {% endif %}

  {% if error %}
  <div class="error-box">{{ error }}</div>
  {% endif %}

  <hr>

  <div class="stats-row">
    <div class="stat">
      <div class="stat-num">{{ rows|length }}</div>
      <div class="stat-label">links</div>
    </div>
    <div class="stat">
      <div class="stat-num">{{ total_hits }}</div>
      <div class="stat-label">total clicks</div>
    </div>
  </div>

  {% if rows %}
  <div class="section-title">Your links</div>
  {% for row in rows %}
  <div class="link-row">
    <a class="short" href="/{{ row['short'] }}">/{{ row['short'] }}</a>
    <span class="arrow">→</span>
    <span class="long">{{ row['long'] }}</span>
    <span class="hits">{{ row['hits'] }} clicks</span>
  </div>
  {% endfor %}
  {% else %}
  <div class="empty">No links yet — add one above!</div>
  {% endif %}

</div>
<script>
  // auto select input on load
  document.querySelector('.url-input').focus();
</script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    short_url = None
    error = None
    conn, cur = get_db()

    if request.method == "POST":
        long_url = request.form["url"].strip()
        if not long_url.startswith("http"):
            long_url = "https://" + long_url
        code = make_code()
        try:
            cur.execute("INSERT INTO urls (short, long) VALUES (%s, %s)", (code, long_url))
            short_url = request.host_url + code
        except Exception as e:
            error = f"Something went wrong: {e}"

    cur.execute("SELECT * FROM urls ORDER BY id DESC")
    rows = cur.fetchall()
    total_hits = sum(row["hits"] for row in rows)
    conn.close()
    return render_template_string(HTML, short_url=short_url, rows=rows,
                                  error=error, total_hits=total_hits)

@app.route("/<code>")
def redirect_url(code):
    conn, cur = get_db()
    cur.execute("SELECT long FROM urls WHERE short = %s", (code,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE urls SET hits = hits + 1 WHERE short = %s", (code,))
        conn.close()
        logger.info(f"Redirect: /{code} → {row['long']}")
        return redirect(row["long"])
    conn.close()
    logger.warning(f"Not found: /{code}")
    return "Link not found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)