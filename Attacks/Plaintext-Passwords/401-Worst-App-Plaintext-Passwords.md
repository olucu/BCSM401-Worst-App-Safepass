tags: 
links: [[401-Worst-App]]

Plaintext Passwörter
```python
db.execute(

"INSERT INTO users (username, password) VALUES (?, ?)", # **KEINE VERSCHLÜSSELUNG!**

(username, password),

)
```

```bash
db.execute(

"INSERT INTO passwords (user_id, site, username, password) VALUES (?,?,?,?)",

(session["user_id"], site, username, password), # **PASSWORT WIRD UNVERSCHLÜSSELT IN DER DATENBANK ABGELEGT!**

)
```

- Benutzer `admin` hat dieses Passwort `admin123`
- Benutzer `alice` hat folgendes Passwort `password`















Sources
[]()