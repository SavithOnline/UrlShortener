import os
import string
import random
import psycopg2
import psycopg2.extras
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

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
    <a href="/{{ row['short'] }}">/{{ row['short'] }}</a> →
    <span style="color:#555">{{ row['long'][:50] }}...</span>
    <span class="hits">({{ row['hits'] }} clicks)</span>
  </p>
{% endfor %}
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
    conn.close()
    return render_template_string(HTML, short_url=short_url, rows=rows, error=error)

@app.route("/<code>")
def redirect_url(code):
    conn, cur = get_db()
    cur.execute("SELECT long FROM urls WHERE short = %s", (code,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE urls SET hits = hits + 1 WHERE short = %s", (code,))
        conn.close()
        return redirect(row["long"])
    conn.close()
    return "Link not found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)