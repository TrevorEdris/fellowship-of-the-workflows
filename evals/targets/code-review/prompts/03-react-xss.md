Review this PR diff for code quality and security issues:

**PR Title:** Add user profile and comments UI
**Files changed:** UserProfile.tsx, CommentList.tsx

```diff
--- /dev/null
+++ b/src/components/UserProfile.tsx
@@ -0,0 +1,42 @@
+import React from "react";
+
+interface UserProfileProps {
+  user: {
+    name: string;
+    email: string;
+    bio: string;
+    joinDate: string;
+    avatarUrl: string;
+  };
+}
+
+export function UserProfile({ user }: UserProfileProps) {
+  const memberDuration = React.useMemo(() => {
+    const joined = new Date(user.joinDate);
+    const months = Math.floor(
+      (Date.now() - joined.getTime()) / (1000 * 60 * 60 * 24 * 30)
+    );
+    return months < 12 ? `${months} months` : `${Math.floor(months / 12)} years`;
+  }, [user.joinDate]);
+
+  return (
+    <div style={{ padding: "1rem", maxWidth: 600, margin: "0 auto" }}>
+      <img
+        src={user.avatarUrl}
+        alt={`${user.name}'s avatar`}
+        style={{ width: 80, height: 80, borderRadius: "50%" }}
+      />
+      <h2>{user.name}</h2>
+      <p>{user.email}</p>
+      <div dangerouslySetInnerHTML={{ __html: user.bio }} />
+      <span style={{
+        color: memberDuration.includes("year") ? "#22c55e" : "#94a3b8",
+        fontWeight: memberDuration.includes("year") ? 600 : 400,
+      }}>
+        Member for {memberDuration}
+      </span>
+    </div>
+  );
+}

--- /dev/null
+++ b/src/components/CommentList.tsx
@@ -0,0 +1,28 @@
+import React from "react";
+
+interface Comment {
+  id: string;
+  author: string;
+  text: string;
+  createdAt: string;
+}
+
+interface CommentListProps {
+  comments: Comment[];
+}
+
+export function CommentList({ comments }: CommentListProps) {
+  if (comments.length === 0) {
+    return <p>No comments yet.</p>;
+  }
+
+  return (
+    <ul>
+      {comments.map((comment) => (
+        <li>
+          <strong>{comment.author}</strong>: {comment.text}
+          <time dateTime={comment.createdAt}>{new Date(comment.createdAt).toLocaleDateString()}</time>
+        </li>
+      ))}
+    </ul>
+  );
+}
```
