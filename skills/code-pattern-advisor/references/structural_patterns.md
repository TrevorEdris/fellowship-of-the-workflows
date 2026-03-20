# Structural Patterns Reference

Structural patterns deal with how classes and objects are composed to form larger
structures. They use inheritance and composition to create flexible, efficient
relationships between entities.

The core question: **Do I have an interface mismatch, a complexity problem, or a
composition problem?** Each structural pattern addresses one of these.

---

## Adapter

**Purpose:** Convert the interface of a class into another interface that clients expect.
Lets classes work together that couldn't otherwise because of incompatible interfaces.

**When to use:**
- You need to integrate a third-party library or legacy system whose interface doesn't
  match what your code expects
- You're migrating from one API to another and need a compatibility layer during the
  transition
- You want to create a reusable class that cooperates with unrelated or unforeseen
  classes (classes that don't necessarily have compatible interfaces)

**When NOT to use:**
- You own both interfaces and can just change one of them. Adapter is for when you
  CAN'T change the interface you're adapting (third-party, legacy, compiled library).
- The "adaptation" is trivial (renaming a method). Consider if a simple wrapper function
  suffices instead of a full Adapter class.
- You're adapting more than one interface at once. That might be Anti-Corruption Layer
  territory, or it might indicate a deeper design problem.

**Common misapplications:**
- Creating Adapters between your own classes within the same codebase. If you control
  both sides, fix the interfaces instead.
- Adapter that does business logic beyond pure translation. An Adapter should translate
  calls and data, not add behavior. If it's adding behavior, it's becoming a Decorator
  or Service.

**Costs:** One additional class per adapted interface. If you have many adapters, the
translation logic can become a maintenance burden.

---

## Bridge

**Purpose:** Decouple an abstraction from its implementation so that the two can vary
independently.

**When to use:**
- You have two independent dimensions of variation (e.g., shape AND rendering engine,
  or platform AND feature set) and don't want a class explosion from combining them
- You need to switch implementations at runtime
- Changes in the implementation should not affect clients of the abstraction

**When NOT to use:**
- There's only one dimension of variation. Bridge exists specifically for the case where
  you have TWO orthogonal hierarchies. With one, prefer simpler patterns (Strategy,
  dependency injection).
- The "implementation" doesn't actually vary. If there's only one implementation now and
  no credible reason to expect another, Bridge is speculative generality.

**Common misapplications:**
- Confusing Bridge with Adapter. Adapter makes incompatible things work together after
  the fact. Bridge is designed upfront to keep abstraction and implementation separate.
- Creating a Bridge where Strategy (simpler, doesn't require parallel hierarchies) would
  suffice.

**Costs:** Increased design complexity. Two parallel hierarchies to maintain. Can be
difficult to understand for developers unfamiliar with the pattern.

---

## Composite

**Purpose:** Compose objects into tree structures to represent part-whole hierarchies.
Lets clients treat individual objects and compositions uniformly.

**When to use:**
- You have a genuine tree/hierarchical structure (file systems, UI component trees,
  organization charts, mathematical expression trees, menu systems)
- Clients should be able to treat leaf and composite nodes the same way
- You want to add new kinds of components without changing existing code

**When NOT to use:**
- Your structure isn't actually a tree. If objects don't have a natural parent-child
  relationship, Composite will feel forced.
- Leaf and composite behaviors are fundamentally different. Composite works best when
  the operations genuinely apply to both levels. If leaf.add(child) is always an error,
  the uniform interface is lying.
- The hierarchy is flat (only one level). A simple list/collection is sufficient.

**Common misapplications:**
- Forcing tree semantics onto data that's naturally flat or relational.
- Making all operations available on all nodes when some operations only make sense for
  composites (e.g., `getChildren()` on a leaf). This can lead to confusing APIs with
  lots of no-op or exception-throwing methods.

**Costs:** Can make it harder to restrict component types (e.g., preventing certain kinds
of children). Type safety can suffer when treating everything uniformly.

---

## Decorator

**Purpose:** Attach additional responsibilities to an object dynamically. Provides a
flexible alternative to subclassing for extending functionality.

**When to use:**
- You need to add behavior to individual objects without affecting other objects of the
  same class
- You want to combine behaviors flexibly (logging + caching + authentication, where any
  combination should be possible)
- Subclassing would lead to a combinatorial explosion of classes
- The extensions should be transparent to clients (same interface as the original)

**When NOT to use:**
- You need to change the object's core interface, not just wrap it. That's an Adapter.
- The "decorations" depend on each other's order in complex ways. Decorator chains where
  ordering matters significantly are hard to debug.
- There's only one combination of behavior you'll ever need. Just create a subclass or
  modify the class directly.
- Your language supports mixins, traits, or extension methods natively. These often
  provide Decorator's benefits more cleanly.

**Common misapplications:**
- Decorator chains that are 5+ levels deep, making debugging a nightmare (where did this
  behavior come from?).
- Using Decorator when the core interface is too large. Every method in the interface
  must be forwarded. If the interface has 20 methods and you only want to intercept 1,
  Decorator is painful. Consider a Proxy or AOP instead.

**Costs:** Many small objects that look alike (hard to debug, hard to introspect). Identity
comparison breaks (decorated object != original). Forwarding boilerplate for every method
in the interface.

---

## Facade

**Purpose:** Provide a simplified, unified interface to a set of interfaces in a subsystem.

**When to use:**
- A subsystem is complex with many interacting classes and you want to provide a simpler
  entry point for common use cases
- You want to reduce coupling between a client and a complex subsystem
- You need to layer your subsystem (each layer has a Facade as its entry point)

**When NOT to use:**
- The subsystem isn't actually complex. Wrapping a single class in another class that
  delegates everything isn't a Facade — it's pointless indirection.
- Clients legitimately need access to the full subsystem API. Facade is for simplifying,
  not restricting.
- You're hiding bad design behind a Facade instead of fixing it. A Facade over a mess
  is still a mess — you've just put a door on it.

**Common misapplications:**
- Using Facade as an excuse not to clean up the underlying subsystem.
- Facade that grows to expose every underlying method, becoming a God Object pass-through.
- Confusing Facade with Adapter. Facade simplifies; Adapter translates.

**Costs:** Can become a bottleneck for subsystem access if not designed carefully. Can
mask performance issues in the subsystem. Risk of the Facade growing too large.

---

## Flyweight

**Purpose:** Share common state across many similar objects to reduce memory consumption.

**When to use:**
- You have a very large number of similar objects (thousands+) consuming significant
  memory
- Most of the object's state can be made extrinsic (passed in from outside) or is shared
  across instances
- The application doesn't depend on object identity (flyweight objects are interchangeable)
- You've profiled and confirmed memory is actually a problem

**When NOT to use:**
- You have a modest number of objects. Flyweight adds complexity; don't optimize memory
  that isn't a problem.
- Object identity matters (each object must be distinguishable by reference).
- The "intrinsic" state is large relative to the "extrinsic" state, meaning sharing
  doesn't save much.

**Common misapplications:**
- Applying Flyweight without profiling. The engineering cost is significant; don't pay
  it without evidence.
- Mutable flyweights. Shared objects must be immutable, or mutation in one context
  corrupts all other contexts sharing the same flyweight.

**Costs:** Increased code complexity. Must carefully separate intrinsic (shared) from
extrinsic (context-dependent) state. Trading memory for computation time (extrinsic state
must be computed or passed around).

---

## Proxy

**Purpose:** Provide a surrogate or placeholder for another object to control access to it.

**When to use:**
- **Lazy initialization** — the real object is expensive to create and might not be needed
- **Access control** — check permissions before delegating to the real object
- **Logging / caching** — intercept calls transparently to add cross-cutting concerns
- **Remote proxy** — represent a remote object locally (RPC, network calls)
- **Smart reference** — additional actions when an object is accessed (reference counting,
  loading from disk on first access)

**When NOT to use:**
- You need to modify the interface, not just control access to it. That's Adapter or
  Decorator.
- The proxy logic is trivial enough to go directly in the client code.
- Your framework provides this natively (many DI frameworks have built-in proxy support;
  Python has `__getattr__`; Rust has `Deref` trait).

**Common misapplications:**
- Proxy that accumulates business logic beyond access control / lifecycle management.
- Confusing Proxy, Decorator, and Adapter. Proxy controls access to the SAME interface.
  Decorator adds behavior to the SAME interface. Adapter converts between DIFFERENT
  interfaces.

**Costs:** Additional indirection on every call. Can make debugging harder (which object
is actually handling this?). Synchronization concerns for thread-safe proxies.
