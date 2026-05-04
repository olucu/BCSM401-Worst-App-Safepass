# SafePass — Worst App Challenge

> **„Deine Passwörter. Sicher. Versprochen." 😈**

Ein Flask-Passwortmanager mit perfektem Marketing und katastrophaler Sicherheit.

**Team Bug Builders:** Joel · Lukas · Andreas
**Modul:** BCSM 401 — Methoden & Techniken der sicheren Softwareentwicklung

---

## Quick Start

```bash
git clone https://github.com/olucu/BCSM401-Worst-App-Safepass.git
cd BCSM401-Worst-App-Safepass
pip install flask flask-unsign --break-system-packages
python3 safepass_app.py
# → http://localhost:5000
```

**Demo-Accounts:**

| User | Passwort |
|---|---|
| `admin` | `admin123` |
| `alice` | `password` |

---

# Teil 1 — Erklärungen

## 1. SQL Injection im Login

### Code

Die SQL-Injection sitzt in der Login-Abfrage:

```python
query = (
    f"SELECT * FROM users WHERE username='{username}' "
    f"AND password='{password}'"
)

user = db.execute(query).fetchone()
```

Hierbei werden Werte aus dem Formular per f-String in den SQL-Befehl eingebaut:

```python
username = request.form.get("username", "")
password = request.form.get("password", "")
```

### Erklärung

Hierdurch ist es möglich, dass ein Benutzer SQL-Code in das Feld `username` oder `password` schreiben kann, der dann Teil der DB-Abfrage wird.

Wird der Username `' OR '1'='1`, dann ergibt das eine Datenbank-Abfrage, in der der Username `''` ODER `'1'='1'` ist und das Passwort `''`:

```sql
SELECT * FROM users
WHERE username='' OR '1'='1'
AND password=''
```

Weil `1=1` immer wahr ist, kann hierdurch die Login-Prüfung manipuliert werden.

### Lösung

Zunächst sollte beim Login in der Relation Username und Passwort als Prepared Statement abgefragt werden, durch Änderung des Codes in:

```python
user = db.execute(
    "SELECT * FROM users WHERE username=? AND password=?",
    (username, password),
).fetchone()
```

Dabei dient das `?` als Platzhalter für die Werte, die in die Datenbank geliefert werden — in diesem Fall 1. der Benutzername und 2. das Passwort.

---

## 2. Plaintext-Passwörter in der Datenbank

### Erklärung

Dieser Code enthält gleich mehrere Schwachstellen.

### Beschreibung

**1. Klartext-Übertragung beim Login.** Der Webserver (Flask) ist derartig eingerichtet, dass dieser unverschlüsselt Anfragen sendet und empfängt:

```python
print("  SafePass läuft auf http://localhost:5000")
```

**2. Klartext in der Datenbank.** Das Passwort liegt im Klartext in der DB:

```python
db.execute(
    "INSERT INTO users (username, password) VALUES ('admin', 'admin123')"
)
db.execute(
    "INSERT INTO users (username, password) VALUES ('alice', 'password')"
)
```

**3. Klartext in der Anzeige.** Das Passwort wird im Template im Klartext ausgegeben:

```html
<table>
  <tr><th>Website</th><th>Username</th><th>Passwort</th></tr>
  {% for p in passwords %}
  <tr>
    <td>{{ p['site'] }}</td>
    <td>{{ p['username'] }}</td>
    <td><code>{{ p['password'] }}</code></td>
  </tr>
  {% endfor %}
</table>
```

### Lösung

**Zu 1.** Die App bereits beim Start mit SSL-Kontext (Zertifikat) — hier in diesem Fall mit einem Test-Zertifikat — ausstatten:

```python
app.run(
    host="0.0.0.0",
    port=5000,
    debug=True,
    ssl_context="adhoc",
)
```

**Zu 2.** Das Passwort sollte gehasht werden. Da Hashing eine Einwegfunktion ist, kann es nicht rückgängig gemacht werden. Im Python-Code benötigt es ein Hash-Werkzeug, welches dafür sorgt, dass Passwörter gehasht in die Datenbank geschrieben werden können. Der angepasste Code könnte so aussehen:

```python
from werkzeug.security import generate_password_hash, check_password_hash

db.execute(
    "INSERT INTO users (username, password) VALUES (?, ?)",
    ("admin", generate_password_hash("admin123")),
)

db.execute(
    "INSERT INTO users (username, password) VALUES (?, ?)",
    ("alice", generate_password_hash("password")),
)
```

Ebenfalls sollte der Code bei der Registrierung angepasst werden in:

```python
db.execute(
    "INSERT INTO users (username, password) VALUES (?, ?)",
    (username, generate_password_hash(password)),
)
```

---

## 3. Hardcoded Secret Key

### Beschreibung

Hier wird der Secret Key zum Signieren von Cookie-Sessions erstellt.

```python
app.secret_key = "1234"
```

### Erklärung

Der `secret_key`, welcher für das Signieren von Session-Cookies verwendet wird, ist hardcoded in der Software, wodurch dieser durch einen Leak oder einen Insider veröffentlicht werden kann.

Außerdem ist der `secret_key`, aufgrund des trivialen Wertes, sehr einfach zu erraten oder per Brute Force zu ermitteln.

Flask speichert den kompletten Session-Inhalt (`user_id`, `username`) in den Cookies und verifiziert die Echtheit mit dem `secret_key`. Wenn der Angreifer diesen Schlüssel hat, kann er seine eigene Session signieren und sich somit ohne Passwort einloggen.

### Lösung

Die Lösung wäre, den `secret_key` aus Umgebungsvariablen oder einem Secret-Manager zu laden. Außerdem sollte man einen sicheren Key verwenden, der nicht leicht zu erraten oder per Brute Force zu ermitteln ist.

---

## 4. Debug-Modus auf `0.0.0.0`

### Code

```python
...
app.run(host="0.0.0.0", port=5000, debug=True)
...
```

### Erklärung

Durch den aktiven Debug-Modus gibt Flask auf der Server-Konsole jede HTTP-Anfrage und die dazugehörige SQL-Query aus. Weil die Login-Query per f-String aus den User-Eingaben gebaut wird (siehe Schwachstelle 1), erscheinen Username und Passwort jedes Login-Versuchs im Klartext direkt im Server-Log.

Außerdem wird beim Start der Debugger-PIN auf der Konsole ausgegeben. Wer Zugriff auf die Logs oder die Konsole hat, kann alle Login-Daten mitlesen.

Außerdem kann sich, durch `host="0.0.0.0"`, jeder im selben Netz mit dem Server verbinden.

### Lösung

Durch `debug=False` kann man die Schwachstelle schließen. Außerdem sollten `print()`-Anweisungen, die SQL-Queries oder andere sensible Werte ausgeben, aus dem Code entfernt werden. In der Entwicklung den Server-Host explizit festlegen: `host="127.0.0.1"`.

---

## 5. Kein Session-Timeout

### Code

```python
session["user_id"]  = user["id"]
session["username"] = user["username"]
# es fehlt: session.permanent = True + app.permanent_session_lifetime = timedelta(...)
```

### Erklärung

Durch das Fehlen eines Session-Timeouts ist jedes Cookie unbegrenzt gültig. Wenn ein Cookie gestohlen wurde, kann man sich jederzeit mit diesem Cookie authentifizieren.

Außerdem sind gefälschte Cookies (aus der Cookie-Forgery) unbegrenzt und dauerhaft gültig.

### Lösung

Durch `app.permanent_session_lifetime = timedelta(minutes=15)` + `session.permanent = True` beim Login kann man diese Schwachstelle schließen.

---

## 6. IDOR — `/all_passwords`

### Code

```python
@app.route("/all_passwords")
def all_passwords():
    if "user_id" not in session:
        return redirect(url_for("login"))
    rows = db.execute("""
        SELECT u.username AS owner, p.site, p.username, p.password
        FROM passwords p JOIN users u ON p.user_id = u.id
    """).fetchall()
    return render_template_string(ALL_PW_TEMPLATE, passwords=rows)
```

### Erklärung

IDOR heißt, dass die App direkt auf Passwörter zugreift, ohne zu überprüfen, wer der Besitzer ist. Dadurch kann jeder Nutzer, der sich in der App authentifizieren kann, alle Passwörter lesen, indem dieser den Endpoint `GET /all_passwords` abfragt.

### Lösung

Überprüfung des Besitzers durch `WHERE p.user_id = :current_user`, bevor man die Passwörter abfragt und anzeigt.

---

## 7. Flask Session Cookie Forgery

### Code

```python
app.secret_key = "1234"
```

Tool installieren:

```bash
pip install flask-unsign --break-system-packages
```

### Erklärung

Durch einen schwachen `secret_key` kann man diesen offline per Brute-Force-Angriff herausfinden. Mit dem `secret_key` kann man dann eigene Session-Cookies signieren und sich somit als beliebiger Nutzer einloggen, ohne dessen Passwort jemals zu kennen.

### Vorgehen

**1. Test-Account anlegen + Session-Cookie kopieren.**

Angreifer registriert einen eigenen Test-Account und kopiert den Session-Cookie aus den Browser-Dev-Tools.

**2. Cookie-Schema anschauen:**

```bash
flask-unsign --decode --cookie "eyJ1c2VybmFtZSI6ImFsaWNlIn0..."
   {'user_id': 2, 'username': 'alice'}
```

**3. Key offline brute-forcen** (mit `rockyou.txt` als Wordlist):

```bash
flask-unsign --unsign --cookie "..." --wordlist rockyou.txt
    Secret key found: 1234
```

**4. Admin-Cookie fälschen:**

```bash
flask-unsign --sign --secret "1234" --cookie "{'user_id': 1, 'username': 'admin'}"
    eyJ1c2VybmFtZSI6ImFkbWluIn0.ZxYz...
```

**5. Cookie einsetzen.**

In den Dev-Tools das gefälschte Session-Cookie einsetzen, dann neu laden. Danach ist man eingeloggt, ohne das Passwort des Nutzers zu kennen.

### Lösung

Der `secret_key` sollte stark und zufällig sein.

---

# Teil 2 — Demo-Walkthrough

In diesem Teil wird Schritt für Schritt mit Screenshots gezeigt, wie die Schwachstellen ausgenutzt werden.

## 1. SQL Injection — Demo

![SQLi 1](Attacks/SQLi-Attack/000001-sqli-attack.png)
![SQLi 2](Attacks/SQLi-Attack/000002-sqli-attack.png)
![SQLi 3](Attacks/SQLi-Attack/000003-sqli-attack.png)
![SQLi 4](Attacks/SQLi-Attack/000004-sqli-attack.png)
![SQLi 5](Attacks/SQLi-Attack/000005-sqli-attack.png)

**Zweite Möglichkeit für SQLi-Attack:**

![SQLi Method 2 — 6](Attacks/SQLi-Attack/000006-sqli-attack-second-method.png)
![SQLi Method 2 — 7](Attacks/SQLi-Attack/000007-sqli-attack-second-method.png)
![SQLi Method 2 — 8](Attacks/SQLi-Attack/000008-sqli-attack-second-method.png)

---

## 4. Debug-Modus — Demo

Login als `alice` mit korrektem Passwort. Anschließend ist auf der Server-Konsole die SQL-Query inkl. Klartext-Passwort sichtbar:

![Debug-Mode 1](Attacks/Debug-Mode/000001-debug-mode-attack.png)
![Debug-Mode 2](Attacks/Debug-Mode/000002-debug-mode-attack.png)
![Debug-Mode 3](Attacks/Debug-Mode/000003-debug-mode-attack.png)
![Debug-Mode 4](Attacks/Debug-Mode/000004-debug-mode-attack.png)

---

## 5. Kein Session-Timeout — Demo

![No Session Timeout 1](Attacks/No-Session-Timeout/000001-no-session-timeout.png)
![No Session Timeout 2](Attacks/No-Session-Timeout/000002-no-session-timeout.png)
![No Session Timeout 3 — alternative Darstellung](Attacks/No-Session-Timeout/000003-no-session-timeout-different-way-of-showcasing.png)

---

## 6. IDOR — Demo

![IDOR 1](Attacks/IDOR/000001-idor-attack.png)
![IDOR 2](Attacks/IDOR/000002-idor-attack.png)
![IDOR 3](Attacks/IDOR/000003-idor-attack.png)
![IDOR 4](Attacks/IDOR/000004-idor-attack.png)
![IDOR 5](Attacks/IDOR/000005-idor-attack.png)
![IDOR 6](Attacks/IDOR/000006-idor-attack.png)
![IDOR 7](Attacks/IDOR/000007-idor-attack.png)
![IDOR 8](Attacks/IDOR/000008-idor-attack.png)
![IDOR 9](Attacks/IDOR/000009-idor-attack.png)
![IDOR 10](Attacks/IDOR/000010-idor-attack.png)
![IDOR 11](Attacks/IDOR/000011-idor-attack.png)
![IDOR 12](Attacks/IDOR/000012-idor-attack.png)
![IDOR 13](Attacks/IDOR/000013-idor-attack.png)
![IDOR 14](Attacks/IDOR/000014-idor-attack.png)

---

## 7. Cookie Forgery — Demo

**Schritt 1 — Test-Account anlegen + Session-Cookie kopieren**

![Cookie Forgery 1](Attacks/Flask-Session-Cookie-Forgery/000001-flask-session-cookie-forgery.png)
![Cookie Forgery 2](Attacks/Flask-Session-Cookie-Forgery/000002-flask-session-cookie-forgery.png)
![Cookie Forgery 3](Attacks/Flask-Session-Cookie-Forgery/000003-flask-session-cookie-forgery.png)
![Cookie Forgery 4](Attacks/Flask-Session-Cookie-Forgery/000004-flask-session-cookie-forgery.png)
![Cookie Forgery 5](Attacks/Flask-Session-Cookie-Forgery/000005-flask-session-cookie-forgery.png)
![Cookie Forgery 6](Attacks/Flask-Session-Cookie-Forgery/000006-flask-session-cookie-forgery.png)
![Cookie Forgery 7](Attacks/Flask-Session-Cookie-Forgery/000007-flask-session-cookie-forgery.png)
![Cookie Forgery 8](Attacks/Flask-Session-Cookie-Forgery/000008-flask-session-cookie-forgery.png)
![Cookie Forgery 9](Attacks/Flask-Session-Cookie-Forgery/000009-flask-session-cookie-forgery.png)
![Cookie Forgery 10](Attacks/Flask-Session-Cookie-Forgery/000010-flask-session-cookie-forgery.png)
![Cookie Forgery 11](Attacks/Flask-Session-Cookie-Forgery/000011-flask-session-cookie-forgery.png)
![Cookie Forgery 12](Attacks/Flask-Session-Cookie-Forgery/000012-flask-session-cookie-forgery.png)

**Schritt 2 — Cookie-Schema anschauen**

![Cookie Forgery 20](Attacks/Flask-Session-Cookie-Forgery/000020-flask-session-cookie-forgery.png)
![Cookie Forgery 21](Attacks/Flask-Session-Cookie-Forgery/000021-flask-session-cookie-forgery.png)
![Cookie Forgery 22](Attacks/Flask-Session-Cookie-Forgery/000022-flask-session-cookie-forgery.png)
![Cookie Forgery 23](Attacks/Flask-Session-Cookie-Forgery/000023-flask-session-cookie-forgery.png)

**Schritt 3 — Key offline brute-forcen**

![Cookie Forgery 13](Attacks/Flask-Session-Cookie-Forgery/000013-flask-session-cookie-forgery.png)
![Cookie Forgery 14](Attacks/Flask-Session-Cookie-Forgery/000014-flask-session-cookie-forgery.png)
![Cookie Forgery 15](Attacks/Flask-Session-Cookie-Forgery/000015-flask-session-cookie-forgery.png)
![Cookie Forgery 16](Attacks/Flask-Session-Cookie-Forgery/000016-flask-session-cookie-forgery.png)
![Cookie Forgery 17](Attacks/Flask-Session-Cookie-Forgery/000017-flask-session-cookie-forgery.png)
![Cookie Forgery 18](Attacks/Flask-Session-Cookie-Forgery/000018-flask-session-cookie-forgery.png)
![Cookie Forgery 19](Attacks/Flask-Session-Cookie-Forgery/000019-flask-session-cookie-forgery.png)
![Cookie Forgery 24](Attacks/Flask-Session-Cookie-Forgery/000024-flask-session-cookie-forgery.png)
![Cookie Forgery 25](Attacks/Flask-Session-Cookie-Forgery/000025-flask-session-cookie-forgery.png)

**Schritt 4 — Admin-Cookie fälschen**

![Cookie Forgery 26](Attacks/Flask-Session-Cookie-Forgery/000026-flask-session-cookie-forgery.png)
![Cookie Forgery 27](Attacks/Flask-Session-Cookie-Forgery/000027-flask-session-cookie-forgery.png)
![Cookie Forgery 28](Attacks/Flask-Session-Cookie-Forgery/000028-flask-session-cookie-forgery.png)

**Schritt 5 — Gefälschtes Cookie im Browser einsetzen**

![Cookie Forgery 29](Attacks/Flask-Session-Cookie-Forgery/000029-flask-session-cookie-forgery.png)
![Cookie Forgery 30](Attacks/Flask-Session-Cookie-Forgery/000030-flask-session-cookie-forgery.png)
![Cookie Forgery 31](Attacks/Flask-Session-Cookie-Forgery/000031-flask-session-cookie-forgery.png)
![Cookie Forgery 32](Attacks/Flask-Session-Cookie-Forgery/000032-flask-session-cookie-forgery.png)
![Cookie Forgery 33](Attacks/Flask-Session-Cookie-Forgery/000033-flask-session-cookie-forgery.png)

---

## Architektur-Skizze (Excalidraw)

→ [`401-Worst-App.excalidraw.png`](401-Worst-App.excalidraw.png)

---

## Quellen & Weiterlesen

- OWASP Top 10 2021: A01 Broken Access Control · A02 Cryptographic Failures · A03 Injection · A07 Identification & Authentication Failures
- Flask-Docs: [Sessions](https://flask.palletsprojects.com/en/latest/quickstart/#sessions), [Werkzeug-Debugger PIN](https://werkzeug.palletsprojects.com/en/latest/debug/)
- `flask-unsign`: <https://github.com/Paradoxis/Flask-Unsign>
