import sqlite3
import string
import random
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)
DB = "urls.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short TEXT UNIQUE NOT NULL,
            long  TEXT NOT NULL,
            hits  INTEGER DEFAULT 0
        )
    """)
    return conn

def make_code():
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=6))

HTML = """
<!doctype html>
<title>URL Shortener</title>
<style>
  body { font-family: sans-serif; max-width: 500px; margin: 60px auto; padding: 0 20px; }
  input[type=text] { width: 100%; padding: 10px; font-size: 16px; box-sizing: border-box; }
  button { margin-top: 10px; padding: 10px 20px; font-size: 16px; cursor: pointer; }
  .result { margin-top: 20px; padding: 14px; background: #f0f9f0; border-radius: 8px; }
  .hits { color: #888; font-size: 13px; }
</style>
<h2>URL Shortener</h2>
<form method="post">
  <input type="text" name="url" placeholder="Paste a long URL here..." required>
  <button type="submit">Shorten</button>
</form>
{% if short_url %}
<div class="result">
  Short URL: <a href="{{ short_url }}">{{ short_url }}</a>
</div>
{% endif %}
{% if error %}
<div class="result" style="background:#fff0f0">{{ error }}</div>
{% endif %}
<hr>
<h3>All links</h3>
{% for row in rows %}
  <p>
    <a href="/{{ row[1] }}">/{{ row[1] }}</a> →
    <span style="color:#555">{{ row[2][:50] }}...</span>
    <span class="hits">({{ row[3] }} clicks)</span>
  </p>
{% endfor %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    short_url = None
    error = None
    db = get_db()

    if request.method == "POST":
        long_url = request.form["url"].strip()
        if not long_url.startswith("http"):
            long_url = "https://" + long_url
        code = make_code()
        try:
            db.execute("INSERT INTO urls (short, long) VALUES (?, ?)", (code, long_url))
            db.commit()
            short_url = request.host_url + code
        except Exception as e:
            error = f"Something went wrong: {e}"

    rows = db.execute("SELECT * FROM urls ORDER BY id DESC").fetchall()
    db.close()
    return render_template_string(HTML, short_url=short_url, rows=rows, error=error)

@app.route("/<code>")
def redirect_url(code):
    db = get_db()
    row = db.execute("SELECT long FROM urls WHERE short = ?", (code,)).fetchone()
    if row:
        db.execute("UPDATE urls SET hits = hits + 1 WHERE short = ?", (code,))
        db.commit()
        db.close()
        return redirect(row[0])
    db.close()
    return "Link not found", 404

import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=False)