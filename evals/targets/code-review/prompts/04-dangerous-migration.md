Review this PR diff for code quality and correctness:

**PR Title:** Add phone number field to user profiles
**Files changed:** migrations/003_add_phone.sql, user_service.py, docs/api.md

```diff
--- /dev/null
+++ b/migrations/003_add_phone.sql
@@ -0,0 +1,2 @@
+-- Add phone number to users table
+ALTER TABLE users ADD COLUMN phone VARCHAR(20);

--- a/user_service.py
+++ b/user_service.py
@@ -15,6 +15,7 @@ class UserService:
         return {
             "id": row.id,
             "email": row.email,
+            "phone": row.phone,
             "created_at": row.created_at.isoformat(),
         }

@@ -25,6 +26,18 @@ class UserService:
         self.db.execute(
             "UPDATE users SET email = %s WHERE id = %s", (email, user_id)
         )
+
+    def update_phone(self, user_id: int, phone: str) -> None:
+        """Update user's phone number."""
+        self.db.execute(
+            "UPDATE users SET phone = %s WHERE id = %s", (phone, user_id)
+        )
+
+    def get_by_phone(self, phone: str) -> dict | None:
+        """Look up user by phone number."""
+        row = self.db.query_one(
+            "SELECT * FROM users WHERE phone = %s", (phone,)
+        )
+        return self._to_dict(row) if row else None

--- a/docs/api.md
+++ b/docs/api.md
@@ -22,3 +22,7 @@ Returns user profile data.
 | email | string | User's email address |
 | created_at | string | ISO 8601 timestamp |

+### PUT /users/:id/phone
+
+Update user's phone number.
```
