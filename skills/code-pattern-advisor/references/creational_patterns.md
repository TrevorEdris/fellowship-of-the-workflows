# Creational Patterns Reference

Creational patterns abstract the instantiation process. They help make a system independent
of how its objects are created, composed, and represented.

The core question for any creational pattern: **Is object construction complex enough,
variable enough, or constrained enough to warrant a dedicated creation mechanism?**
If you can just call a constructor and be done, do that.

---

## Factory Method

**Purpose:** Define an interface for creating objects, but let subclasses or implementations
decide which concrete class to instantiate.

**When to use:**
- You don't know in advance which concrete type you need — the decision depends on
  configuration, user input, or runtime context
- You want to centralize the "which type do I create?" decision so that adding a new
  type requires changing only one place
- You're building a framework or library where users need to extend the creation logic

**When NOT to use:**
- There's only one concrete type and no realistic prospect of adding more. A factory for
  a single class is just an unnecessary layer of indirection.
- The construction is trivial (no parameters, no configuration). Just use `new` or the
  language's equivalent.
- You're adding it "for testability" but you could achieve the same result by passing the
  dependency directly (dependency injection is often simpler than a factory).

**Common misapplications:**
- Creating a `Factory` class that just wraps a constructor call with no branching logic.
  This adds a file and a concept for zero benefit.
- Using Factory Method when Abstract Factory is needed (multiple related objects) or
  vice versa.
- Naming things `XFactory` when the method is really just a static helper / convenience
  constructor. Not everything that creates an object is the Factory Method pattern.

**Costs:** Adds an interface and at least one implementation class per product type.
In languages with first-class functions, a factory function (not class) often suffices.

---

## Abstract Factory

**Purpose:** Provide an interface for creating *families* of related objects without
specifying their concrete classes.

**When to use:**
- You need to create multiple related objects that must be used together (e.g., a UI
  toolkit that produces buttons, scrollbars, and windows that must all be from the same
  theme)
- Your system must be configured for one of several "families" of products
- You want to enforce that products from different families are never mixed

**When NOT to use:**
- You're creating a single type of object, not a family. Use Factory Method instead.
- The families never actually change at runtime. If you always use one family, you've
  built an abstraction nobody will swap.
- The number of product types in the family keeps growing — Abstract Factory becomes
  painful to extend because every new product type requires changes to every factory.

**Common misapplications:**
- Building an Abstract Factory with only one product type. That's just Factory Method
  with extra steps.
- Creating an Abstract Factory for "future flexibility" when there's no indication a
  second family will ever exist.

**Costs:** Can lead to an explosion of classes. Every new product type requires updating
every concrete factory. Consider if simpler approaches (configuration objects, dependency
injection) achieve the same goal.

---

## Builder

**Purpose:** Separate the construction of a complex object from its representation, allowing
the same construction process to create different representations. More commonly used as a
fluent API for constructing objects with many optional parameters.

**When to use:**
- An object has many constructor parameters, most of which are optional, and the
  combinations are too numerous for constructor overloading
- Construction requires multiple steps that may happen in different orders
- You want to enforce that an object is immutable after construction but needs to be
  assembled piece by piece
- The construction process should be reusable for building different representations

**When NOT to use:**
- The object has fewer than ~4 parameters and they're all required. Just use a
  constructor.
- Your language has named/default parameters (Python, Kotlin, Swift, C#). The Builder
  pattern largely exists to compensate for Java's lack of this feature. In Python,
  `MyClass(name="x", size=10, color="red")` is already a "builder" in effect.
- The object is a simple data container. Use a struct, dataclass, record, or equivalent.

**Common misapplications:**
- Building a Builder for a class with 3 fields. This is over-engineering.
- Not making the built object immutable. If the object is mutable after `.build()`, you've
  added complexity without getting the immutability guarantee that makes Builder valuable.
- Creating a Builder that *requires* every field to be set — that's just a verbose
  constructor.

**Language note:** In Java, Builder is essential and idiomatic. In Python (dataclasses +
keyword args), Kotlin (data classes + default params), and Rust (struct initialization +
Default trait), the pattern is largely unnecessary. Check `language_idioms.md`.

**Costs:** Adds a full parallel class (the Builder) for every buildable type. Duplication
of fields between Builder and target. Boilerplate-heavy in languages without code
generation support.

---

## Prototype

**Purpose:** Create new objects by cloning an existing instance rather than constructing
from scratch.

**When to use:**
- Object creation is expensive (database lookups, complex computation, file I/O) and you
  need many similar instances
- You need to create objects whose type isn't known at compile time, but you have an
  instance you can copy
- A system needs to be independent of how its products are created and represented,
  and products are configured at runtime

**When NOT to use:**
- Objects are cheap to construct. Cloning has its own cost (deep copy logic, copying
  internal state correctly) that's only justified when construction is genuinely expensive.
- The object has circular references or complex internal state that makes deep copying
  error-prone.
- The object holds external resources (file handles, database connections, network sockets).
  Cloning these is either meaningless or dangerous.

**Common misapplications:**
- Implementing `clone()` without deep copy semantics, leading to shared mutable state
  between "copies." This is a major bug source.
- Using Prototype when a Factory with configuration would be simpler and safer.

**Costs:** Deep copy logic can be surprisingly complex. Must carefully handle reference
types, circular dependencies, and external resources. Many languages have poor or
footgun-laden clone/copy mechanisms.

---

## Singleton

**Purpose:** Ensure a class has exactly one instance and provide a global point of access
to it.

**When to use — honestly, rarely:**
- Hardware access coordination (a single printer spooler, a single audio device manager)
- Truly shared, truly global configuration that's read-only after initialization
- Logger instances (this is the one case where most developers accept Singleton)

**When NOT to use — most of the time:**
- As a substitute for global variables. If you're using Singleton to make something
  globally accessible, the real problem is your dependency management, not your
  instantiation count.
- For "convenience" access. Just because something is used in many places doesn't mean
  it should be a Singleton. Pass it as a dependency.
- In multithreaded contexts without careful synchronization. Singleton initialization
  in multithreaded environments is a classic source of race conditions.
- When you "might need two someday." If there's any possibility the constraint will
  relax, don't use Singleton.

**Common misapplications:**
- Singleton as a God Object — stuffing unrelated responsibilities into a single instance
  because it's conveniently global.
- Singleton for testability nightmare — Singletons carry state between tests, making
  test isolation difficult or impossible.
- "Everything should be a Singleton" — database connections, configuration, logging,
  caches, services... this is the Golden Hammer anti-pattern.

**Costs:** Hides dependencies (classes depend on the Singleton but this isn't visible in
their interfaces). Makes testing painful. Creates tight coupling. Carries mutable state
globally. Often violated by the need for "just one more instance." In most modern
codebases, dependency injection eliminates the need for Singleton entirely.

---

## Object Pool

**Purpose:** Manage a pool of reusable objects to avoid the cost of repeated creation and
destruction.

**When to use:**
- Object creation is genuinely expensive AND frequent (database connections, threads,
  large buffers, GPU resources)
- The object can be meaningfully "reset" to a clean state for reuse
- You've profiled and confirmed that object creation is actually a bottleneck

**When NOT to use:**
- You haven't profiled. Object creation in modern runtimes is usually fast.
  Don't assume it's a bottleneck.
- The object's "reset" logic is complex or error-prone (risk of leaking state between
  uses)
- The pool management overhead exceeds the savings from reuse

**Common misapplications:**
- Pooling objects that are cheap to create (string buffers, small DTOs). The pool
  management code costs more than the problem it solves.
- Not handling pool exhaustion correctly (what happens when all objects are in use?).
- Leaking state between pool consumers because the reset logic is incomplete.

**Costs:** Pool management complexity (sizing, exhaustion handling, lifecycle management).
Risk of state leaks. Thread-safety concerns if the pool is shared across threads.
