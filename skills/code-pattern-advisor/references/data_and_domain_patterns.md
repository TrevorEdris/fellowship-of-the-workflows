# Data & Domain Patterns Reference

These patterns come primarily from Eric Evans' Domain-Driven Design (DDD) and Martin
Fowler's Patterns of Enterprise Application Architecture (PoEAA). They address how to
model domain logic, manage data access, and maintain integrity across boundaries.

The core question: **How complex is the domain, and how separated do data access and
business logic need to be?**

Important framing: DDD patterns are for genuinely complex domains. If the application is
essentially CRUD (create, read, update, delete) with little business logic, most DDD
patterns will add weight without benefit. There's no shame in CRUD — most applications
are CRUD, and simpler patterns serve them well.

---

## Repository

**Purpose:** Mediate between the domain and data mapping layers using a collection-like
interface for accessing domain objects. Encapsulate the logic for retrieving and storing
aggregates.

**When to use:**
- Your domain model has meaningful business logic and you want to keep it free of
  persistence concerns
- You need to swap or mock the data access layer for testing
- You have aggregate roots (DDD) and want to enforce that persistence happens only
  through them
- Multiple parts of the application need to query the same entities in different ways

**When NOT to use:**
- The application is CRUD-heavy with little domain logic. Repository over a simple ORM
  is just a pass-through wrapper that adds a file and achieves nothing.
- You're using a framework that already provides repository-like abstractions (Spring
  Data repositories, Django's ORM Manager, Rails Active Record). Don't wrap the wrapper.
- You find yourself creating a `GenericRepository<T>` with only `GetById`, `Save`,
  `Delete`. This is the ORM's job, not yours.
- You're following CQRS — on the read side, repositories are often unnecessary; direct
  queries or thin read models are simpler and more performant.

**Common misapplications:**
- Repository that exposes IQueryable or raw query builders, leaking the persistence
  abstraction it was supposed to hide.
- One repository per table instead of per aggregate root. Repositories should correspond
  to domain boundaries, not database tables.
- Repository methods that return entities with partially loaded data, creating unexpected
  null fields downstream.

**Costs:** Extra abstraction layer. Can become a bottleneck as query needs grow (the
repository interface keeps expanding). Risk of hiding important query performance concerns
behind a simple-looking interface.

---

## Value Object

**Purpose:** An object that represents a descriptive aspect of the domain with no
conceptual identity. Two Value Objects are equal if all their attributes are equal.

**When to use:**
- The concept is defined by its attributes, not by an identity. Money(10, "USD") is the
  same as any other Money(10, "USD") — there's no "which specific ten dollars" question.
- You want to encapsulate validation and behavior with the value (e.g., an EmailAddress
  type that validates format at construction)
- You want immutability guarantees — the value cannot be changed after creation, only
  replaced
- Classic examples: Money, DateRange, Address, Coordinates, EmailAddress, Color,
  Temperature, Percentage

**When NOT to use:**
- The concept has a lifecycle and needs to be tracked over time. That's an Entity.
- The value is a simple primitive with no validation or behavior worth encapsulating.
  Wrapping every `int` and `string` in a Value Object is over-engineering.
- Equality semantics are complex or context-dependent (two addresses might be "the same"
  in one context but different in another if apartment number matters).

**Common misapplications:**
- Mutable Value Objects. By definition, Value Objects must be immutable. If you need to
  change one, create a new instance. A mutable Value Object is just a data class with
  confused semantics.
- Value Objects with identity fields (IDs, database keys). If it has an ID, it's an
  Entity.
- Value Objects that are too granular (wrapping `string name` in a `Name` class that adds
  nothing beyond the wrapper).
- Value Objects that are too coarse (an Address Value Object that contains an entire
  Customer's worth of data).

**Language note:** Many modern languages provide excellent Value Object support natively:
Java `record`, Kotlin `data class`, C# `record struct`, Python `@dataclass(frozen=True)`
or `NamedTuple`, Rust structs with `#[derive(PartialEq, Eq)]`.

**Costs:** Creating new instances for every "change" can be performance-sensitive in
tight loops (though this is rarely an actual problem in practice). Equality comparison
logic must be implemented correctly.

---

## Entity

**Purpose:** An object defined primarily by its identity rather than its attributes. An
Entity persists over time and through state changes — it's the SAME entity even if every
attribute changes.

**When to use:**
- The concept has a lifecycle: it's created, it changes, and it may be deleted, but it
  maintains continuity throughout
- Two instances with identical attributes are NOT the same thing (two people both named
  "John Smith" are different people)
- You need to track, reference, and persist this object by its identity
- Classic examples: User, Order, Account, Product, Patient, Vehicle

**When NOT to use:**
- The concept is fully described by its attributes with no need for identity tracking.
  That's a Value Object.
- The object is a data transfer container with no behavior. That's a DTO.
- You're creating an Entity for every database table regardless of whether the concept
  has meaningful identity and behavior. This leads to an Anemic Domain Model.

**Common misapplications:**
- Anemic Entities that are just bags of getters/setters with no behavior. Business logic
  should live on Entities (and Value Objects), not exclusively in Services.
- Entities that compare equal by attributes instead of by identity.
- Entities without enforced invariants — allowing invalid state by exposing all setters.

**Costs:** Identity management (generating, storing, and comparing IDs). Lifecycle
complexity. Must carefully define what "same identity" means in each context.

---

## Aggregate Root

**Purpose:** A cluster of domain objects that are treated as a single unit for data
changes. External references only point to the root; the root enforces all invariants
for the cluster.

**When to use:**
- A group of objects must change together to maintain consistency (an Order and its
  OrderItems must be consistent at all times)
- You need to define clear transactional boundaries (what gets saved together)
- You want to prevent external code from directly manipulating child objects in ways
  that could violate business rules

**When NOT to use:**
- Your domain doesn't have genuine consistency requirements across related objects.
  Not every parent-child relationship is an aggregate.
- Every entity becomes its own aggregate root. This usually means the aggregates are too
  small and you're over-fragmenting the domain.
- Aggregates are too large (loading one aggregate loads half the database). A common
  rule of thumb: if deleting the root wouldn't logically delete the children, the
  children probably don't belong in this aggregate.

**Common misapplications:**
- Aggregates that are too big — containing entities that have independent lifecycles.
  If the child entity could meaningfully exist without the root, it's probably its own
  aggregate.
- Crossing aggregate boundaries in a single transaction. Each transaction should affect
  one aggregate. Cross-aggregate consistency should use eventual consistency (domain
  events).
- Treating aggregate design as a database modeling exercise instead of a domain modeling
  exercise.

**Costs:** Must carefully size aggregates (too small = fragmented consistency, too large =
contention and performance issues). Eventually consistency across aggregates adds
complexity.

---

## DTO (Data Transfer Object)

**Purpose:** An object that carries data between processes or layers. Contains no business
logic — just data.

**When to use:**
- You need to transfer data across a boundary (network, process, layer) and the domain
  model isn't appropriate for the other side
- The consumer needs a different shape of data than the domain model provides (e.g., a
  flattened view, a subset of fields, aggregated data)
- You want to decouple the API contract from the internal domain model so they can
  evolve independently

**When NOT to use:**
- There's no boundary. If the DTO is used within the same module that has the domain
  model, you're adding a mapping step for no reason.
- The DTO is identical to the domain model. If you're just copying every field from
  Entity to DTO and back, question whether the DTO is serving a purpose.
- As a substitute for domain modeling. "We just use DTOs everywhere" is an Anemic Domain
  Model in disguise.

**Common misapplications:**
- DTOs with business logic (validation, computed properties, state management). A DTO
  should be inert.
- Nested DTOs that mirror the entire domain model graph, defeating the purpose of having
  a separate transfer representation.
- One-to-one DTO-per-entity mapping with no actual transformation. This is cargo cult
  architecture.

**Costs:** Mapping code between DTOs and domain objects (tedious, error-prone). Can
proliferate if not managed (request DTOs, response DTOs, internal DTOs...).

---

## Data Mapper

**Purpose:** A layer of mappers that moves data between objects and a database while
keeping them independent of each other and the mapper itself.

**When to use:**
- Domain objects should have no knowledge of the database schema
- The domain model and database schema differ significantly
- You need full control over SQL / queries / persistence logic
- Complex mapping scenarios (inheritance hierarchies, polymorphic queries)

**When NOT to use:**
- The domain model maps 1:1 to the database schema. Active Record is simpler.
- You're using an ORM that already implements Data Mapper (Hibernate, SQLAlchemy,
  Entity Framework). Don't re-implement what the ORM provides.
- The application is simple CRUD with no complex domain logic.

**Costs:** Significant implementation effort. Must maintain mapping code as both domain
and schema evolve. Most teams should use an ORM that implements this pattern rather than
building it from scratch.

---

## Active Record

**Purpose:** An object that wraps a row in a database table, encapsulates database access,
and adds domain logic on that data.

**When to use:**
- Domain logic is simple — mostly CRUD with straightforward validations
- The domain model maps closely to the database schema
- You want rapid development with minimal ceremony (common in Rails, Django, Laravel)
- The application is small to medium sized

**When NOT to use:**
- Domain logic is complex and doesn't align with database structure. Active Record
  couples domain and persistence, which becomes painful when they diverge.
- You need to test domain logic without a database. Active Record objects inherently
  depend on database connectivity.
- The domain model needs to be shared across multiple persistence mechanisms.

**Common misapplications:**
- Active Record objects with hundreds of lines of business logic, becoming God Objects
  that mix persistence, validation, business rules, and presentation concerns.
- Using Active Record in a codebase that's outgrown it but not migrating because
  "it's always been this way."

**Costs:** Tight coupling between domain and persistence. Hard to unit test without a
database. Can lead to bloated model classes. Not appropriate for complex domains.

---

## CQRS (Command Query Responsibility Segregation)

**Purpose:** Separate read operations (queries) from write operations (commands) into
distinct models, allowing each to be optimized independently.

**When to use:**
- Read and write patterns are significantly different (e.g., writes go to a normalized
  domain model, reads need denormalized views)
- Read-heavy systems where query performance must be optimized independently
- Complex domain models where the write model is necessarily complex but reads should
  be simple
- When combined with Event Sourcing for audit trails and temporal queries

**When NOT to use:**
- Simple CRUD applications. CQRS adds significant complexity; don't pay for it unless
  read/write asymmetry actually exists.
- Small teams that can't maintain the additional infrastructure and mental model.
- When you'd be creating two models that are basically identical. If the read model is
  just a SELECT * from the write model, CQRS is overhead.

**Common misapplications:**
- "Full CQRS" (separate databases, event sourcing, eventual consistency) when "light
  CQRS" (separate read/write classes, same database) would suffice.
- CQRS everywhere instead of just in the bounded contexts that need it.
- Underestimating the eventual consistency complexity on the read side.

**Costs:** Increased complexity (two models to maintain). Eventual consistency challenges.
Infrastructure overhead if using separate data stores. Overkill for simple domains.

---

## Unit of Work

**Purpose:** Maintain a list of objects affected by a business transaction and coordinate
the writing out of changes and the resolution of concurrency problems.

**When to use:**
- Multiple objects need to be persisted atomically as part of a single business operation
- You want to batch database writes for performance
- You need change tracking (know which objects are dirty, new, or deleted)

**When NOT to use:**
- Your ORM already implements Unit of Work (Entity Framework's DbContext, Hibernate's
  Session, SQLAlchemy's Session). These ARE Units of Work. Don't wrap them.
- Each operation touches only one aggregate. The aggregate root can manage its own
  persistence.
- You're not using a relational database, or your data store has its own transaction
  model.

**Costs:** Complexity of change tracking. Memory overhead for tracking modifications.
Must handle concurrency conflicts. Usually provided by your ORM — implementing from
scratch is rarely justified.

---

## Specification

**Purpose:** Encapsulate a business rule into a composable, reusable, testable object.
Can be used for validation, filtering, and object creation.

**When to use:**
- The same business rule needs to be applied in multiple contexts (validation AND
  database filtering AND UI display)
- Complex query predicates that should be composable (AND, OR, NOT combinations)
- Business rules that domain experts can name and discuss

**When NOT to use:**
- The rule is used in only one place. A simple predicate function or method is clearer.
- You're using CQRS. Specification encourages a single model for reads and writes,
  which conflicts with CQRS's separated models.
- The specification becomes a thin wrapper around a SQL WHERE clause with no additional
  domain meaning.

**Costs:** Can be over-engineered for simple cases. Composability adds abstraction layers.
Potential tension with CQRS (see references for details).

---

## Anti-Corruption Layer (ACL)

**Purpose:** A translation layer between your bounded context and an external system,
preventing the external system's model from leaking into your domain.

**When to use:**
- Integrating with a legacy system whose model doesn't match yours
- Consuming a third-party API whose concepts don't align with your domain language
- During a migration where old and new systems coexist
- When two bounded contexts within the same organization have different models for
  overlapping concepts

**When NOT to use:**
- The external system's model is close enough to yours that translation is trivial
  (a simple rename or field mapping). An Adapter may suffice.
- You control both systems and can align their models directly.
- The ACL would be a single class with one method. That's just a mapping function,
  not a layer.

**Common misapplications:**
- ACL that grows to contain business logic beyond translation.
- Not updating the ACL when the external system changes, leading to silent data
  corruption or lost information.

**Costs:** Must be maintained as both systems evolve. Adds latency. Additional service
to monitor and deploy.

---

## Domain Event

**Purpose:** A record of something significant that happened in the domain. Used to
trigger side effects, communicate between aggregates, and maintain audit trails.

**When to use:**
- A change in one aggregate should trigger actions in other aggregates or bounded contexts
- You need eventual consistency between aggregates (instead of transactional consistency)
- Audit trail requirements (what happened, when, in what order)
- Integration between microservices or bounded contexts

**When NOT to use:**
- Everything can be handled within a single aggregate's transaction boundary.
  Domain events add infrastructure complexity.
- The "events" are just method calls in disguise with no subscribers beyond the
  immediate handler. If there's always exactly one handler, it's a method call.
- The team isn't prepared for eventual consistency and the debugging challenges of
  asynchronous event-driven systems.

**Costs:** Infrastructure (event bus, message broker). Eventual consistency complexity.
Event ordering and idempotency challenges. Debugging async flows is harder than
synchronous calls.
