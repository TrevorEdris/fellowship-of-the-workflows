# Firestore Patterns

## Data Modeling Principles

Firestore is a document database. The rules for relational modeling don't apply.

### Rule 1: Design for Your Query Patterns

Structure collections to match access patterns, not normalized data models.

```
# Bad: normalized (requires joins — Firestore has none)
orders/{orderId}
  userId: "user_123"
  items: [itemId1, itemId2]  # requires second query per item

# Good: denormalized (co-located, single query)
orders/{orderId}
  userId: "user_123"
  items:
    - id: "item_1"
      name: "Widget"
      price: 9.99
    - id: "item_2"
      name: "Gadget"
      price: 14.99
```

### Rule 2: Subcollections vs Arrays

| Use | When |
|-----|------|
| Array | Bounded list (< 100 items), always read with the document |
| Subcollection | Unbounded list, queried independently, or written individually |
| Nested map | Small structured data, always read with the document |

```
users/{userId}
  name: "Alice"
  roles: ["admin", "billing"]       ← array: bounded, co-read
  addressHistory:                    ← subcollection: unbounded
    {addressId}/
      street: "123 Main St"
      updatedAt: timestamp
  preferences:                       ← nested map: small, co-read
    theme: "dark"
    notifications: true
```

### Rule 3: Avoid Large Documents

Documents > 1 MB have performance implications. Aim for < 100 KB per document.

## Queries

```python
# Python — basic query
from google.cloud import firestore

db = firestore.Client()

# Simple filter
docs = db.collection("orders") \
    .where("status", "==", "pending") \
    .stream()

# Compound filter (requires composite index in firestore.indexes.json)
docs = db.collection("orders") \
    .where("userId", "==", user_id) \
    .where("status", "==", "pending") \
    .order_by("createdAt", direction=firestore.Query.DESCENDING) \
    .limit(10) \
    .stream()

# Range query
docs = db.collection("products") \
    .where("price", ">=", 10.0) \
    .where("price", "<=", 50.0) \
    .stream()

# Array contains
docs = db.collection("users") \
    .where("roles", "array_contains", "admin") \
    .stream()
```

**Composite indexes are required** for queries that combine:
- Filters on multiple fields
- Filter + order by a different field
- Two or more inequality filters

Firestore will throw an error with a URL to create the missing index.

## Indexes

```json
// firestore.indexes.json
{
  "indexes": [
    {
      "collectionGroup": "orders",
      "queryScope": "COLLECTION",
      "fields": [
        {"fieldPath": "userId", "order": "ASCENDING"},
        {"fieldPath": "status", "order": "ASCENDING"},
        {"fieldPath": "createdAt", "order": "DESCENDING"}
      ]
    }
  ]
}
```

```bash
# Deploy indexes
firebase deploy --only firestore:indexes
```

## Transactions

```python
# Python — read-write transaction (serializable)
from google.cloud import firestore

db = firestore.Client()

@firestore.transactional
def transfer_credits(transaction, from_ref, to_ref, amount):
    from_doc = from_ref.get(transaction=transaction)
    to_doc = to_ref.get(transaction=transaction)

    if from_doc.get("credits") < amount:
        raise ValueError("Insufficient credits")

    transaction.update(from_ref, {"credits": firestore.Increment(-amount)})
    transaction.update(to_ref, {"credits": firestore.Increment(amount)})

transaction = db.transaction()
transfer_credits(transaction, from_ref, to_ref, 100)
```

```python
# Batch writes (not transactional across documents — use for bulk writes)
batch = db.batch()
for item in items:
    ref = db.collection("products").document(item["id"])
    batch.set(ref, item)
batch.commit()  # All writes in one RPC
```

## Security Rules

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Users can only read/write their own document
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;

      // User can read their own orders; admin can read all
      match /orders/{orderId} {
        allow read: if request.auth != null &&
          (request.auth.uid == userId || request.auth.token.admin == true);
        allow write: if request.auth != null && request.auth.uid == userId;
      }
    }

    // Products: anyone can read; only admins can write
    match /products/{productId} {
      allow read: if true;
      allow write: if request.auth != null && request.auth.token.admin == true;

      // Validate data shape on create
      allow create: if request.resource.data.keys().hasAll(["name", "price"]) &&
        request.resource.data.price is number &&
        request.resource.data.price > 0;
    }
  }
}
```

```bash
# Deploy security rules
firebase deploy --only firestore:rules

# Test rules with emulator
firebase emulators:start --only firestore
```

## Real-Time Listeners

```python
# Python — snapshot listener (blocks thread; use in a background thread)
def on_snapshot(doc_snapshot, changes, read_time):
    for doc in doc_snapshot:
        print(f"Updated: {doc.id} = {doc.to_dict()}")

doc_ref = db.collection("orders").document(order_id)
doc_watch = doc_ref.on_snapshot(on_snapshot)

# Stop listener when done
doc_watch.unsubscribe()
```

## Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| Querying all documents and filtering client-side | Create server-side indexes, use `.where()` clauses |
| Documents > 1 MB | Split into subcollections |
| Using auto-increment IDs | Use `.add()` (Firestore generates random IDs) or UUIDs |
| Transactions for single-document writes | Use `document.update()` with `Increment` / `ArrayUnion` |
| No composite indexes for compound queries | Add to `firestore.indexes.json` and deploy |
| Firestore for analytics queries | Export to BigQuery for analytics |
| Real-time listeners in server-side code | Use listeners only in client SDKs; poll or use Eventarc triggers server-side |
