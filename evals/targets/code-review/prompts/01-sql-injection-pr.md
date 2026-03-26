Review this PR diff for code quality and security issues:

**PR Title:** Add user authentication endpoint
**Files changed:** auth_service.py, auth_routes.py

```diff
--- /dev/null
+++ b/auth_service.py
@@ -0,0 +1,35 @@
+import hashlib
+import sqlite3
+
+DB_PATH = "app.db"
+
+
+def get_db():
+    return sqlite3.connect(DB_PATH)
+
+
+def find_user_by_email(email: str) -> dict | None:
+    db = get_db()
+    cursor = db.cursor()
+    cursor.execute(f"SELECT id, email, password_hash FROM users WHERE email = '{email}'")
+    row = cursor.fetchone()
+    if not row:
+        return None
+    return {"id": row[0], "email": row[1], "password_hash": row[2]}
+
+
+def verify_password(plain: str, hashed: str) -> bool:
+    computed = hashlib.sha256(plain.encode()).hexdigest()
+    return computed == hashed
+
+
+def authenticate(email: str, password: str) -> dict | None:
+    user = find_user_by_email(email)
+    if not user:
+        return None
+    if not verify_password(password, user["password_hash"]):
+        return None
+    return {"id": user["id"], "email": user["email"]}

--- /dev/null
+++ b/auth_routes.py
@@ -0,0 +1,18 @@
+from flask import Flask, request, jsonify
+from auth_service import authenticate
+
+app = Flask(__name__)
+
+
+@app.route("/login", methods=["POST"])
+async def login():
+    data = request.get_json()
+    email = data.get("email")
+    password = data.get("password")
+
+    user = authenticate(email, password)
+    if not user:
+        return jsonify({"error": "Invalid credentials"}), 401
+
+    return jsonify({"user_id": user["id"], "token": "placeholder"})
```
