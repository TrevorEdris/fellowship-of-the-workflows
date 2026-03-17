# Spanner Patterns

## Schema Design Rules

### Rule 1: Avoid Hotspot Row Keys

Spanner distributes data by row key. Monotonic keys (auto-increment, timestamp prefix) route all writes to the same split node — creating hotspots.

```sql
-- BAD: auto-increment creates hotspot writes
CREATE TABLE Orders (
  OrderId INT64 NOT NULL,  -- Sequential — all writes go to same server
  ...
) PRIMARY KEY (OrderId);

-- GOOD: UUID distributes writes across splits
CREATE TABLE Orders (
  OrderId STRING(36) NOT NULL,  -- UUID prefix distributes writes
  ...
) PRIMARY KEY (OrderId);

-- GOOD: Bit-reversal or hash prefix for timestamp-prefixed keys
CREATE TABLE Events (
  -- Reverse the timestamp bits to prevent hotspots
  TimestampRev INT64 NOT NULL,  -- computed: REVERSE(TIMESTAMP)
  EventId STRING(36) NOT NULL,
  ...
) PRIMARY KEY (TimestampRev, EventId);
```

### Rule 2: Interleave Child Tables in Parent

Co-locates child rows with their parent on the same split — dramatically reduces cross-split reads.

```sql
CREATE TABLE Users (
  UserId STRING(36) NOT NULL,
  Name STRING(MAX),
  Email STRING(320),
  CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
) PRIMARY KEY (UserId);

-- Interleaved child table: stored adjacent to parent rows
CREATE TABLE Orders (
  UserId STRING(36) NOT NULL,
  OrderId STRING(36) NOT NULL,
  Status STRING(20),
  TotalAmount NUMERIC,
  CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
) PRIMARY KEY (UserId, OrderId),
  INTERLEAVE IN PARENT Users ON DELETE CASCADE;

CREATE TABLE OrderItems (
  UserId STRING(36) NOT NULL,
  OrderId STRING(36) NOT NULL,
  ItemId STRING(36) NOT NULL,
  Quantity INT64,
  Price NUMERIC,
) PRIMARY KEY (UserId, OrderId, ItemId),
  INTERLEAVE IN PARENT Orders ON DELETE CASCADE;
```

Reading a user's orders is now a single tablet scan, not a cross-split join.

### Rule 3: Secondary Indexes

```sql
-- Index for querying orders by status
CREATE INDEX OrdersByStatus ON Orders(Status) STORING (CreatedAt, TotalAmount);

-- Interleaved index (co-locates with parent, efficient for parent-scoped queries)
CREATE INDEX OrdersByUserStatus ON Orders(UserId, Status)
  INTERLEAVE IN Users;
```

## Transactions

```go
// Go — read-write transaction (serializable, globally consistent)
import "cloud.google.com/go/spanner"

_, err = client.ReadWriteTransaction(ctx, func(ctx context.Context, txn *spanner.ReadWriteTransaction) error {
    // Read
    row, err := txn.ReadRow(ctx, "Users", spanner.Key{userID}, []string{"Balance"})
    if err != nil {
        return err
    }
    var balance int64
    if err := row.Column(0, &balance); err != nil {
        return err
    }

    if balance < amount {
        return fmt.Errorf("insufficient balance")
    }

    // Buffer mutations (not applied until commit)
    txn.BufferWrite([]*spanner.Mutation{
        spanner.Update("Users",
            []string{"UserId", "Balance"},
            []interface{}{userID, balance - amount},
        ),
    })
    return nil
})
```

```go
// Read-only transaction (for queries that don't need to write — more efficient)
ro := client.ReadOnlyTransaction()
defer ro.Close()

iter := ro.Query(ctx, spanner.Statement{
    SQL: `SELECT OrderId, Status, TotalAmount
          FROM Orders
          WHERE UserId = @userId AND Status = @status
          ORDER BY CreatedAt DESC LIMIT 10`,
    Params: map[string]interface{}{
        "userId": userID,
        "status": "pending",
    },
})
defer iter.Stop()

for {
    row, err := iter.Next()
    if err == iterator.Done {
        break
    }
    // process row
}
```

## DML vs Mutations

| | DML (SQL) | Mutations |
|---|---|---|
| **Syntax** | `INSERT`, `UPDATE`, `DELETE` SQL | `spanner.Insert`, `spanner.Update`, `spanner.Mutation` |
| **Visibility within txn** | Reads after DML see the written data | Mutations are buffered; not visible in same txn |
| **Performance** | Slightly slower (round trip) | Faster (batched at commit) |
| **Use for** | Complex conditional writes, need to read after write | Bulk writes, simple updates |

```go
// DML — use when you need to read the updated value in the same transaction
stmt := spanner.Statement{
    SQL: `UPDATE Users SET Balance = Balance - @amount WHERE UserId = @userId`,
    Params: map[string]interface{}{"amount": 100, "userId": userID},
}
rowCount, err := txn.Update(ctx, stmt)
```

## Partitioned DML (Bulk Updates)

```go
// Partitioned DML: run UPDATE/DELETE across many rows without a single txn
// Runs as multiple smaller transactions — not atomically consistent
rowCount, err := client.PartitionedUpdate(ctx, spanner.Statement{
    SQL: `UPDATE Orders SET Status = 'archived' WHERE CreatedAt < @cutoff`,
    Params: map[string]interface{}{"cutoff": time.Now().AddDate(0, -6, 0)},
})
```

## Backup and PITR

```bash
# Create a manual backup
gcloud spanner backups create my-backup \
  --instance=my-instance \
  --database=my-db \
  --expiration-date=$(date -d "+7 days" --iso-8601)

# List backups
gcloud spanner backups list --instance=my-instance

# Restore to a new database
gcloud spanner databases restore new-db \
  --instance=my-instance \
  --source-backup=my-backup

# Enable PITR (retained for up to 7 days)
gcloud spanner databases update my-db \
  --instance=my-instance \
  --version-retention-period=7d
```

## Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| Sequential/timestamp-based primary keys | Use UUID or hash-prefix |
| Not interleaving child tables | INTERLEAVE IN PARENT for parent-child relationships |
| Large transactions (> 80,000 mutations) | Break into smaller batches |
| DML for bulk writes (> 10k rows) | Use Partitioned DML or batch mutations |
| Auto-commit mode for multi-step operations | Use explicit `ReadWriteTransaction` |
| Spanner for < 1TB / < 1000 QPS | Use Cloud SQL — Spanner is expensive at this scale |
| Using string UUIDs without padding concern | Verify UUIDs are case-consistent (lowercase) |
