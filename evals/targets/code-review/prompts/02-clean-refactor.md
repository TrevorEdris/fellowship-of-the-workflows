Review this PR diff for code quality issues:

**PR Title:** cleanup stuff
**PR Description:** (empty)
**Files changed:** db/pool.go

```diff
--- a/db/pool.go
+++ b/db/pool.go
@@ -1,45 +1,38 @@
 package db

 import (
 	"context"
 	"database/sql"
+	"fmt"
 	"sync"
 	"time"
 )

-var (
-	pool     *sql.DB
-	poolOnce sync.Once
-	poolErr  error
-)
-
-func GetPool() (*sql.DB, error) {
-	poolOnce.Do(func() {
-		pool, poolErr = sql.Open("postgres", connStr())
-		if poolErr != nil {
-			return
-		}
-		pool.SetMaxOpenConns(25)
-		pool.SetMaxIdleConns(5)
-		pool.SetConnMaxLifetime(5 * time.Minute)
-	})
-	return pool, poolErr
+// Pool wraps sql.DB with health checking and graceful shutdown.
+type Pool struct {
+	db   *sql.DB
+	once sync.Once
 }

-func connStr() string {
-	return "postgres://localhost:5432/myapp?sslmode=disable"
+// New creates a connection pool with sensible defaults.
+func New(dsn string) (*Pool, error) {
+	db, err := sql.Open("postgres", dsn)
+	if err != nil {
+		return nil, fmt.Errorf("open db: %w", err)
+	}
+	db.SetMaxOpenConns(25)
+	db.SetMaxIdleConns(5)
+	db.SetConnMaxLifetime(5 * time.Minute)
+	return &Pool{db: db}, nil
 }

-func Ping() error {
-	db, err := GetPool()
-	if err != nil {
-		return err
-	}
-	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
+// Health checks the connection pool is alive.
+func (p *Pool) Health(ctx context.Context) error {
+	ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
 	defer cancel()
 	return db.PingContext(ctx)
 }

-func Close() error {
-	if pool != nil {
-		return pool.Close()
-	}
-	return nil
+// Close shuts down the pool. Safe to call multiple times.
+func (p *Pool) Close() error {
+	var err error
+	p.once.Do(func() { err = p.db.Close() })
+	return err
 }
```
