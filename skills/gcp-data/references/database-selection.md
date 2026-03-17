# GCP Database Selection Guide

## Decision Matrix

| Use Case | First Choice | Second Choice | Avoid |
|----------|-------------|---------------|-------|
| Traditional relational app (<10TB) | Cloud SQL (PostgreSQL) | Cloud SQL (MySQL) | Spanner (cost) |
| Global writes, planet-scale OLTP | Spanner | AlloyDB | Cloud SQL (single-region) |
| PostgreSQL + ML/vector search | AlloyDB | Cloud SQL + pgvector | — |
| Serverless document store | Firestore | Cloud Datastore | — |
| Real-time sync / offline-first | Firestore | — | Cloud SQL |
| Wide-column, time-series, >1PB | Bigtable | — | Firestore (query limits) |
| Object/file storage | Cloud Storage (GCS) | — | Any database |
| Cache / session store | Memorystore (Redis) | Memorystore (Valkey) | Cloud SQL |
| Data warehouse / analytics | BigQuery | — | Cloud SQL, Firestore |
| Message queue / event streaming | Pub/Sub | Cloud Tasks | Cloud SQL |

## Cloud SQL (PostgreSQL / MySQL / SQLServer)

**Choose Cloud SQL when:**
- Existing application uses relational SQL
- Single-region is sufficient
- Team knows SQL; no need for NoSQL modeling
- Using ORMs (SQLAlchemy, GORM, Prisma) with existing schemas

**Limits:**
- Single primary per instance (read replicas for read scale)
- Storage up to 64TB per instance
- Not designed for multi-region writes (use Spanner for that)

**Configuration quick-ref:**
- PostgreSQL 16 recommended for new instances
- Use Private IP + Cloud SQL Auth Proxy (no public IP in production)
- Enable IAM database authentication for Cloud Run / GKE services
- Point-in-time recovery + automated backups mandatory in production

## Cloud SQL AlloyDB

**Choose AlloyDB when:**
- Need PostgreSQL-compatible database
- Requiring ML/vector search capabilities (pgvector built-in)
- Need faster analytics than Cloud SQL (columnar engine built-in)
- 99.99% availability SLA required (vs 99.95% for Cloud SQL)

**Limits:**
- 4x–100x faster for OLAP vs Cloud SQL PostgreSQL (built-in columnar engine)
- More expensive than Cloud SQL (~3x for comparable instance sizes)
- Preview MCP server available (Cloud SQL-compatible connection patterns)

## Spanner

**Choose Spanner when:**
- Multi-region writes required (global OLTP)
- Horizontal scale beyond what Cloud SQL handles
- 99.999% availability required (5 nines)
- Strongly consistent global transactions are a business requirement

**Limits:**
- Expensive: minimum ~$900/month for a single-region, 1-node instance
- No auto-increment PKs (use UUID or hash-prefix)
- SQL dialect differences from standard PostgreSQL/MySQL
- Learning curve for schema design (interleaving, hotspot avoidance)

**When NOT to use Spanner:**
- < 1TB data or < 1000 QPS — Cloud SQL is cheaper and simpler
- Startup or cost-sensitive project — Cloud SQL first, migrate later if needed

## Firestore

**Choose Firestore when:**
- Document-oriented data model (hierarchical, schemaless)
- Serverless — no instance management, scales to zero
- Real-time listeners needed (mobile / web clients with live updates)
- Firebase SDK for mobile/web apps

**Limits:**
- 1MB per document maximum
- Limited query support: no server-side joins, no LIKE queries, no full-text search
- Composite indexes must be explicitly created for multi-field queries
- Not suitable for analytics (use BigQuery export for that)

**Firestore vs Datastore:**
- Firestore in Native mode: for new projects (real-time, mobile, multi-region)
- Firestore in Datastore mode: for existing Datastore workloads (not recommended for new projects)

## Bigtable

**Choose Bigtable when:**
- Wide-column time-series data (IoT telemetry, click stream, financial tick data)
- Petabyte-scale reads/writes
- Sub-10ms P99 latency at scale
- MapReduce / analytics workloads

**Limits:**
- No SQL, no secondary indexes, no multi-row transactions
- Row key design is critical — bad key design = hotspots
- Minimum meaningful cost starts at ~$500/month
- Not for OLTP, not for document storage

## Cloud Storage (GCS)

**Use GCS when:**
- Storing files, blobs, binary objects
- Archiving data (ARCHIVE and COLDLINE storage classes)
- Staging data for pipelines (source/sink for BigQuery, Dataflow, Cloud Functions)
- Static website hosting
- Backup and disaster recovery storage

**Not a database** — no query capability (except BigQuery external tables). Use for data that's read/written as a whole object.

## Memorystore (Redis / Valkey)

**Choose Memorystore when:**
- Cache layer (session store, computed result cache)
- Rate limiting (atomic INCR/DECR)
- Pub/Sub-like messaging with persistence (Redis Streams)
- Leaderboards and sorted sets

**Redis vs Valkey:**
- Redis (Standard): mature, large ecosystem, most team familiarity
- Valkey: open-source Redis fork, same protocol — use if you prefer avoiding Redis Ltd licensing concerns

**Important:** Memorystore is VPC-only. Cloud Run requires Serverless VPC Access connector for egress.

## Cost Reference (approximate, us-central1, mid-2025)

| Service | Minimum monthly cost | At scale |
|---------|---------------------|----------|
| Cloud SQL (db-g1-small) | ~$25 | $200–$2000+ |
| AlloyDB (2 vCPU) | ~$375 | $1000–$5000+ |
| Spanner (1 node, 1 region) | ~$900 | $900/node/region |
| Firestore | $0 (free tier) | $0.06/100k reads |
| Bigtable (1 node) | ~$450 | $0.17/node/hr |
| GCS | $0 (per GB) | $0.02/GB/month |
| Memorystore (1 GB Basic) | ~$35 | $35+/GB |
