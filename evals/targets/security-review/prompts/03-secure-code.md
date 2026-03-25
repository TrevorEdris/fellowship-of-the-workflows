Review this code for security vulnerabilities:

```python
from flask import Flask, request, jsonify, g
from functools import wraps
import sqlite3
import bcrypt
import secrets

app = Flask(__name__)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("app.db")
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        db = get_db()
        session = db.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > datetime('now')",
            (token,),
        ).fetchone()
        if not session:
            return jsonify({"error": "Invalid or expired token"}), 401
        g.user_id = session["user_id"]
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    user = db.execute(
        "SELECT id, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()

    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = secrets.token_urlsafe(32)
    db.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, datetime('now', '+24 hours'))",
        (user["id"], token),
    )
    db.commit()
    return jsonify({"token": token})

@app.route("/profile")
@require_auth
def profile():
    db = get_db()
    user = db.execute(
        "SELECT id, email, name FROM users WHERE id = ?", (g.user_id,)
    ).fetchone()
    return jsonify(dict(user))
```
