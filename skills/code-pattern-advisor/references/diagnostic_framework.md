# Diagnostic Framework

Before recommending any pattern, work through these questions. Infer what you can from
context — ask only what's ambiguous.

## Step 1: Identify the Problem Category

What kind of structural tension exists?

| Signal | Category | Reference |
|--------|----------|-----------|
| Complex or varying object construction | **Creation** | `creational_patterns.md` |
| Incompatible interfaces or complex subsystem | **Structure** | `structural_patterns.md` |
| Objects communicating, reacting, or coordinating | **Behavior** | `behavioral_patterns.md` |
| Data access, persistence, or domain integrity | **Data & Domain** | `data_and_domain_patterns.md` |
| Errors, nulls, or chaining fallible operations | **Functional** | `functional_patterns.md` |
| Pattern feels wrong, forced, or overcomplicated | **Misapplication** | `anti_patterns.md` |

## Step 2: Assess the Context

These factors dramatically change which pattern (if any) is appropriate:

**Language & paradigm.** Many GoF patterns exist to work around limitations of specific
languages. Strategy is a lambda in Python/JS/Kotlin. Visitor is pattern matching in
Rust/F#/Scala. Iterator is built into virtually every modern language. Check
`language_idioms.md` before recommending a GoF pattern — if the language has a native
feature that replaces it, recommend the idiom, not the pattern.

**Scale & team size.** A solo developer writing a 500-line script does not need Repository,
Unit of Work, or CQRS. Patterns add indirection. Indirection has a cost. That cost is only
justified when the codebase is large enough, changes frequently enough, or is maintained
by enough people that the indirection pays for itself in reduced coupling.

**Axis of change.** The single most important question in pattern selection: *what changes
most often in this code?* The pattern should encapsulate the axis of change behind a stable
interface. If you encapsulate the wrong axis, you've added complexity without benefit.

**Existing conventions.** If the codebase already uses a particular architectural style
(e.g., Active Record everywhere), introducing a competing pattern (e.g., Data Mapper) in
one module creates inconsistency that's worse than either choice alone. Consistency within
a codebase matters more than theoretical optimality.

## Step 3: Recommend (or Don't)

Your recommendation must include:

1. **Pattern name and one-sentence purpose** — what structural problem it solves
2. **Why it fits this specific situation** — tied to the diagnostic signals above
3. **What it costs** — every pattern has tradeoffs; name them honestly
4. **When to abandon it** — the signals that mean this pattern has outlived its usefulness
5. **What NOT to do with it** — the most common misapplication of this specific pattern

If no pattern is warranted, say so explicitly and explain why the simpler approach is
better. "Just use a function" or "just use a plain class" are valid recommendations.

## Step 4: Provide Implementation Guidance

- Use the language the user is working in. If unknown, ask or use pseudocode.
- Show the MINIMAL version first. Don't gold-plate the example.
- If the pattern interacts with other patterns (e.g., Repository + Unit of Work, or
  Builder + Fluent Interface), mention the combination but don't implement both unless asked.
- Name things clearly. The pattern structure should be obvious from names alone.

## Pattern Quick-Reference

For triage only — use the category reference files for full guidance.

### Creation
- **Factory Method** — defer instantiation to subclasses
- **Abstract Factory** — families of related objects without specifying concrete classes
- **Builder** — complex construction with many optional parts
- **Prototype** — clone existing objects instead of constructing from scratch
- **Singleton** — exactly one instance (use sparingly; usually a code smell)
- **Object Pool** — reuse expensive objects instead of creating/destroying repeatedly

### Structure
- **Adapter** — make incompatible interfaces work together
- **Bridge** — separate abstraction from implementation so both can vary
- **Composite** — treat individual objects and compositions uniformly (tree structures)
- **Decorator** — add behavior dynamically without subclassing
- **Facade** — simplified interface to a complex subsystem
- **Flyweight** — share state across many similar objects to save memory
- **Proxy** — control access, add lazy loading, or add logging around an object

### Behavior
- **Chain of Responsibility** — pass request along a chain until something handles it
- **Command** — encapsulate a request as an object (enables undo, queuing, logging)
- **Iterator** — traverse a collection without exposing its internals
- **Mediator** — centralize complex communication between many objects
- **Memento** — capture and restore object state (snapshots)
- **Observer** — notify dependents when state changes
- **State** — change behavior when internal state changes (state machines)
- **Strategy** — swap algorithms at runtime behind a common interface
- **Template Method** — define algorithm skeleton; let subclasses fill in steps
- **Visitor** — add operations to objects without modifying their classes

### Data & Domain
- **Repository** — abstract data access behind a collection-like interface
- **Value Object** — immutable, identity-less objects compared by attributes
- **Entity** — objects with unique identity that persists across state changes
- **Aggregate Root** — consistency boundary around a cluster of domain objects
- **DTO** — transfer data across boundaries without domain logic
- **Data Mapper** — separate domain objects from persistence logic entirely
- **Active Record** — domain objects that know how to persist themselves
- **CQRS** — separate read models from write models
- **Unit of Work** — track changes across multiple operations, commit atomically
- **Specification** — encapsulate business rules as composable, reusable objects
- **Anti-Corruption Layer** — translate between your model and a foreign system's model

### Functional & Error-Handling
- **Result / Either** — represent success or failure without exceptions
- **Option / Maybe** — represent presence or absence without null
- **Railway-Oriented Programming** — chain fallible operations on a two-track model
- **Monad (general)** — chain computations while managing context/effects
