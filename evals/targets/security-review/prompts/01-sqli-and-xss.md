Review this code for security vulnerabilities:

```python
import hashlib
import jwt
from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)
SECRET_KEY = "my-super-secret-key-2024"

def get_db():
    return sqlite3.connect("app.db")

@app.route("/user/<user_id>")
def get_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = cursor.fetchone()
    if not user:
        return "Not found", 404
    return {"id": user[0], "name": user[1], "email": user[2]}

@app.route("/search")
def search():
    query = request.args.get("q", "")
    results = do_search(query)
    return render_template_string(
        f"<h1>Results for: {query}</h1><ul>{''.join(f'<li>{r}</li>' for r in results)}</ul>"
    )

def cache_key(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

@app.route("/api/token")
def get_token():
    user_id = request.args.get("user_id")
    token = jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm="HS256")
    return {"token": token}

if __name__ == "__main__":
    app.run(debug=False)
```
