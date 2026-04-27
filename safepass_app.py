"""
 ____         __      ____
/ ___|  __ _ / _| ___|  _ \ __ _ ___ ___
\___ \ / _` | |_ / _ \ |_) / _` / __/ __|
 ___) | (_| |  _|  __/  __/ (_| \__ \__ \
|____/ \__,_|_|  \___|_|   \__,_|___/___/

  🔓 SafePass – "Deine Passwörter. Sicher. Versprochen." 🔓
  Bug Builders | BCM-401 | Worst App Challenge

  ⚠️  WARNUNG: Dieser Code ist ABSICHTLICH UNSICHER.
  ⚠️  Bitte NIEMALS produktiv einsetzen!

  Schwachstellen:
  [1] SQL Injection         – kein Prepared Statement im Login
  [2] Plaintext Passwörter  – keine Hashing-Funktion
  [3] Hardcoded Secret Key  – "1234" im Source Code
  [4] Debug-Modus aktiv     – Flask läuft mit debug=True
  [5] Kein HTTPS            – alles über HTTP
  [6] Kein Session-Timeout  – Sitzung läuft ewig
  [7] Session-Cookie-Fälschung – Secret Key erlaubt beliebige Sessions

  Exploit für [7]:
    pip install flask-unsign
    flask-unsign --unsign --cookie "<cookie>" --wordlist rockyou.txt
    flask-unsign --sign --secret "1234" --cookie "{'user_id': 1, 'username': 'admin'}"
    → Gefälschtes Cookie im Browser einsetzen = Admin ohne Login!
"""

from flask import Flask, request, session, redirect, url_for, render_template_string, g
import sqlite3
import os

# ─────────────────────────────────────────────────────────────────────────────
# [VULN 3+7] Hardcoded Secret Key → Session-Cookie-Fälschung!
#
#   1) pip install flask-unsign
#   2) Key cracken:
#        flask-unsign --unsign --cookie "<cookie>" --wordlist rockyou.txt
#        → findet "1234" in Millisekunden
#   3) Admin-Session fälschen:
#        flask-unsign --sign --secret "1234" --cookie "{'user_id': 1, 'username': 'admin'}"
#   4) Cookie im Browser ersetzen → Admin ohne Login! 🎯
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "1234"  # 💀 Hardcoded – steht in rockyou.txt an Position ~50

DATABASE = "safepass.db"


# ─────────────────────────────────────────────────────────────────────────────
# Datenbank-Setup
# ─────────────────────────────────────────────────────────────────────────────
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL,
                site     TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL        -- [VULN 2] Klartext!
            )
        """)
        # Demo-User anlegen (Passwort im Klartext gespeichert)
        existing = db.execute("SELECT * FROM users WHERE username='admin'").fetchone()
        if not existing:
            # [VULN 2] Passwort wird NICHT gehasht
            db.execute(
                "INSERT INTO users (username, password) VALUES ('admin', 'admin123')"
            )
            db.execute(
                "INSERT INTO users (username, password) VALUES ('alice', 'password')"
            )
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# HTML-Templates (inline für Einfachheit)
# ─────────────────────────────────────────────────────────────────────────────
BASE_STYLE = """
<style>
  body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto;
         padding: 20px; background: #f5f5f5; }
  .card { background: white; padding: 30px; border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,.1); margin-bottom: 20px; }
  input[type=text], input[type=password] {
    width: 100%; padding: 10px; margin: 8px 0 16px;
    border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;
  }
  button { background: #3b82f6; color: white; padding: 10px 24px;
           border: none; border-radius: 4px; cursor: pointer; font-size: 15px; }
  button:hover { background: #2563eb; }
  .danger { background: #fee2e2; border: 1px solid #fca5a5;
            padding: 10px; border-radius: 4px; margin-bottom: 12px; color: #991b1b; }
  .vuln  { background: #fef3c7; border-left: 4px solid #f59e0b;
            padding: 8px 12px; margin: 4px 0; font-size: 13px; }
  table  { width: 100%; border-collapse: collapse; }
  th, td { padding: 10px; text-align: left; border-bottom: 1px solid #e5e7eb; }
  th     { background: #f9fafb; font-weight: 600; }
  a      { color: #3b82f6; text-decoration: none; }
  nav    { margin-bottom: 20px; }
  nav a  { margin-right: 16px; }
</style>
"""

LOGIN_TEMPLATE = BASE_STYLE + """
<div class="card">
  <h2>🔓 SafePass – Login</h2>
  <p style="color:#6b7280">Deine Passwörter. Sicher. Versprochen.</p>
  {% if error %}
  <div class="danger">{{ error }}</div>
  {% endif %}
  <div class="vuln">⚠️ Tipp für Angreifer: Probiere als Username:  <code>' OR '1'='1</code></div>
  <form method="POST">
    <label>Username</label>
    <input type="text" name="username" placeholder="Username" autofocus>
    <label>Passwort</label>
    <input type="password" name="password" placeholder="Passwort">
    <button type="submit">Einloggen</button>
  </form>
  <p style="margin-top:16px"><a href="/register">Noch kein Konto? Registrieren</a></p>
</div>
"""

REGISTER_TEMPLATE = BASE_STYLE + """
<div class="card">
  <h2>📝 Registrieren</h2>
  {% if error %}<div class="danger">{{ error }}</div>{% endif %}
  <form method="POST">
    <label>Username</label>
    <input type="text" name="username" placeholder="Username">
    <label>Passwort</label>
    <input type="password" name="password" placeholder="Passwort">
    <button type="submit">Konto erstellen</button>
  </form>
  <p><a href="/login">Zurück zum Login</a></p>
</div>
"""

DASHBOARD_TEMPLATE = BASE_STYLE + """
<div class="card">
  <nav>
    <a href="/dashboard">🏠 Dashboard</a>
    <a href="/add">➕ Passwort hinzufügen</a>
    <a href="/all_passwords">🔍 ALLE Passwörter (Admin-Bug)</a>
    <a href="/logout">Logout</a>
  </nav>
  <h2>Willkommen, {{ username }}! 👋</h2>
  <div class="vuln">⚠️ [VULN 6] Kein Session-Timeout – du bleibst für immer eingeloggt.</div>
  <div class="vuln">⚠️ [VULN 5] Verbindung läuft über HTTP – alles ist im Klartext übertragbar.</div>

  <h3>Deine gespeicherten Passwörter</h3>
  {% if passwords %}
  <table>
    <tr><th>Website</th><th>Username</th><th>Passwort</th></tr>
    {% for p in passwords %}
    <tr>
      <td>{{ p['site'] }}</td>
      <td>{{ p['username'] }}</td>
      <td><code>{{ p['password'] }}</code></td>  {# [VULN 2] Klartext! #}
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p style="color:#6b7280">Noch keine Passwörter gespeichert.</p>
  {% endif %}
</div>
"""

ADD_TEMPLATE = BASE_STYLE + """
<div class="card">
  <h2>➕ Passwort hinzufügen</h2>
  {% if success %}<div style="background:#d1fae5;padding:10px;border-radius:4px;margin-bottom:12px">✅ Gespeichert!</div>{% endif %}
  <div class="vuln">⚠️ [VULN 2] Passwort wird OHNE Verschlüsselung gespeichert.</div>
  <form method="POST">
    <label>Website</label>
    <input type="text" name="site" placeholder="z.B. github.com">
    <label>Username</label>
    <input type="text" name="username" placeholder="Username">
    <label>Passwort</label>
    <input type="password" name="password" placeholder="Passwort">
    <button type="submit">Speichern</button>
  </form>
  <p><a href="/dashboard">← Zurück</a></p>
</div>
"""

ALL_PW_TEMPLATE = BASE_STYLE + """
<div class="card">
  <h2>🚨 ALLE Passwörter aller User</h2>
  <div class="danger">
    ⚠️ <strong>IDOR-Schwachstelle</strong>: Diese Seite ist für alle eingeloggten
    User erreichbar – keine Rollen, kein Admin-Check!
  </div>
  <table>
    <tr><th>User</th><th>Website</th><th>Username</th><th>Passwort (Klartext!)</th></tr>
    {% for p in passwords %}
    <tr>
      <td>{{ p['owner'] }}</td>
      <td>{{ p['site'] }}</td>
      <td>{{ p['username'] }}</td>
      <td><code style="color:#dc2626">{{ p['password'] }}</code></td>
    </tr>
    {% endfor %}
  </table>
  <p><a href="/dashboard">← Zurück</a></p>
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Routen
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        db = get_db()

        # ─────────────────────────────────────────────────────────────────
        # [VULN 1] SQL INJECTION – Benutzereingabe direkt in Query!
        # Beispiel-Payload: username = ' OR '1'='1
        # ─────────────────────────────────────────────────────────────────
        query = (
            f"SELECT * FROM users WHERE username='{username}' "
            f"AND password='{password}'"
        )
        print(f"[DEBUG] SQL Query: {query}")  # auch das ist schlecht

        user = db.execute(query).fetchone()

        if user:
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            # [VULN 6] Kein session.permanent + SESSION_LIFETIME gesetzt
            return redirect(url_for("dashboard"))
        else:
            error = "Falscher Username oder Passwort."

    return render_template_string(LOGIN_TEMPLATE, error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Bitte alle Felder ausfüllen."
        else:
            db = get_db()
            # [VULN 2] Passwort im Klartext gespeichert, kein bcrypt/hashing
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password),
            )
            db.commit()
            return redirect(url_for("login"))

    return render_template_string(REGISTER_TEMPLATE, error=error)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    passwords = db.execute(
        "SELECT * FROM passwords WHERE user_id=?", (session["user_id"],)
    ).fetchall()

    return render_template_string(
        DASHBOARD_TEMPLATE,
        username=session.get("username"),
        passwords=passwords,
    )


@app.route("/add", methods=["GET", "POST"])
def add_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    success = False
    if request.method == "POST":
        site     = request.form.get("site", "")
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        db = get_db()
        # [VULN 2] Passwort direkt, unverschlüsselt in die DB
        db.execute(
            "INSERT INTO passwords (user_id, site, username, password) VALUES (?,?,?,?)",
            (session["user_id"], site, username, password),
        )
        db.commit()
        success = True

    return render_template_string(ADD_TEMPLATE, success=success)


@app.route("/all_passwords")
def all_passwords():
    """
    [VULN] IDOR (Insecure Direct Object Reference) + fehlende Autorisierung:
    Jeder eingeloggte User kann ALLE Passwörter aller User sehen.
    Kein Admin-Check, keine Rollen.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    rows = db.execute("""
        SELECT u.username AS owner, p.site, p.username, p.password
        FROM passwords p
        JOIN users u ON p.user_id = u.id
    """).fetchall()

    return render_template_string(ALL_PW_TEMPLATE, passwords=rows)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─────────────────────────────────────────────────────────────────────────────
# App starten
# [VULN 4] debug=True – gibt Stack Traces + interaktive Shell im Browser preis!
# [VULN 5] host='0.0.0.0' + kein HTTPS – alles über unverschlüsseltes HTTP
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("\n" + "="*55)
    print("  🔓  SafePass läuft auf http://localhost:5000")
    print("  ⚠️   Teste SQL Injection:  ' OR '1'='1")
    print("  ⚠️   Alle Schwachstellen aktiv!")
    print("="*55 + "\n")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,   # [VULN 4] Debug-Modus!
    )
