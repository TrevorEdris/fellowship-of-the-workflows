# Language Idioms Reference

Many GoF patterns were designed for C++ and Smalltalk in 1994. Modern languages have
absorbed the best ideas as first-class features, making the pattern's ceremonial form
unnecessary.

**Rule:** If the language has a native feature that provides the pattern's benefit, use
the native feature. Don't impose a Java-shaped pattern on Python or a C++-shaped pattern
on Rust.

This reference maps patterns to the native features that replace them, per language.

---

## Strategy Pattern → First-Class Functions

The Strategy pattern encapsulates an algorithm behind an interface so it can be swapped.
In languages with first-class functions, passing a function IS the Strategy pattern.

| Language | Native Alternative |
|----------|-------------------|
| **Python** | Pass a function/lambda. `sorted(data, key=lambda x: x.name)` |
| **JavaScript/TypeScript** | Pass a function/arrow function. Callbacks are idiomatic. |
| **Rust** | Pass a closure or function pointer. `Fn` traits. |
| **Go** | Pass a function value. Function types are first-class. |
| **Kotlin** | Lambdas, function types `(T) -> R` |
| **Swift** | Closures |
| **C++** | `std::function`, lambdas (C++11+), function pointers |
| **C#** | Delegates, lambdas, `Func<T, R>` |
| **Java** | Lambdas (Java 8+), though interface-based Strategy is still idiomatic for multi-method strategies |

**When the formal pattern is still warranted:** When the "strategy" is a cluster of
related methods that must be swapped together (not just one function). In that case, an
interface with an implementation class is still the right approach in any language.

---

## Iterator Pattern → Language Iteration Protocols

Every modern language has a built-in iteration protocol. You almost never implement the
GoF Iterator from scratch.

| Language | Native Protocol |
|----------|----------------|
| **Python** | `__iter__` / `__next__`, generator functions (`yield`) |
| **JavaScript/TypeScript** | `Symbol.iterator`, generator functions (`function*`) |
| **Rust** | `Iterator` trait, `.iter()` / `.into_iter()` |
| **Go** | `range` keyword; iterators via channels or func-based patterns (Go 1.23 range-over-func) |
| **Kotlin** | `Iterable`, `Iterator`, sequence builders |
| **Swift** | `Sequence` / `IteratorProtocol` |
| **C++** | Iterator concept, `begin()`/`end()`, ranges (C++20) |
| **C#** | `IEnumerable<T>` / `IEnumerator<T>`, `yield return` |
| **Java** | `Iterable<T>` / `Iterator<T>`, `Stream` API |

**When custom iteration logic is still needed:** When traversing a custom data structure
(graph, tree, skip list) that doesn't map to a simple sequence. Even then, implement the
language's protocol, not the GoF interface.

---

## Visitor Pattern → Pattern Matching

Visitor exists to add operations to a type hierarchy without modifying the types. Languages
with pattern matching or algebraic data types provide this natively.

| Language | Native Alternative |
|----------|-------------------|
| **Rust** | `match` on enums (algebraic data types). This is the idiomatic approach. |
| **Scala** | `match` / case classes |
| **F#** | `match` on discriminated unions |
| **Haskell** | Pattern matching on ADTs |
| **Kotlin** | `when` on sealed classes |
| **C#** | Switch expressions with pattern matching (C# 8+), sealed types (C# 11+) |
| **Python** | `match` / `case` (3.10+) on dataclasses or simple types |
| **Swift** | `switch` on enums with associated values |
| **Java** | Pattern matching for switch (Java 21+), sealed classes (Java 17+) |
| **C++** | `std::visit` on `std::variant` (C++17), though it's verbose |

**When Visitor is still warranted:** When the language lacks pattern matching or algebraic
data types (older Java, C, C++ without variant). Also when you need double dispatch
specifically (rare in practice).

---

## Observer Pattern → Reactive / Event Systems

Most frameworks provide Observer as a built-in mechanism.

| Language / Framework | Native Alternative |
|---------------------|-------------------|
| **JavaScript** | DOM events, EventEmitter, RxJS, Signals |
| **React** | State management (useState, useContext, Zustand, Redux) |
| **Vue** | Reactivity system (ref, reactive, watch, computed) |
| **Kotlin** | Kotlin Flow, StateFlow, SharedFlow |
| **Swift** | Combine framework, @Published, ObservableObject |
| **C#** | Events/delegates, Rx.NET, INotifyPropertyChanged |
| **Java** | PropertyChangeListener, RxJava, Spring Events |
| **Python** | Signals (Django, Blinker), asyncio event patterns |
| **Rust** | Channels (mpsc), tokio broadcast, event crates |

**When raw Observer is still useful:** When you're building a library/framework itself
and can't depend on a reactive framework, or in embedded/constrained environments.

---

## Builder Pattern → Named/Default Parameters

Builder exists primarily because Java lacks named and default parameters. Languages that
have them often don't need Builder.

| Language | Native Alternative |
|----------|-------------------|
| **Python** | Keyword arguments + `@dataclass` / `@dataclass(frozen=True)` |
| **Kotlin** | Data classes + named arguments + default values |
| **Swift** | Structs with memberwise initializers + default values |
| **C#** | Object initializer syntax + `record` types |
| **Rust** | Struct initialization + `Default` trait + builder crates when needed |
| **TypeScript** | Object spread / destructuring with defaults |
| **Scala** | Case classes + named/default parameters |
| **Java** | Builder is still idiomatic and often necessary (Lombok's @Builder helps) |
| **C++** | Designated initializers (C++20), but Builder is still common for complex construction |

**When Builder is still warranted in these languages:**
- Construction involves validation or multi-step initialization that can't be expressed
  as simple parameter defaults
- Immutability is enforced (the built object can't be modified, but Builder accumulates
  changes)
- The construction process itself varies (GoF's original intent: same process, different
  representations)

---

## Singleton Pattern → Dependency Injection

Singleton is rarely needed in applications that use dependency injection.

| Language / Framework | DI Alternative |
|---------------------|---------------|
| **Java / Spring** | `@Component` + `@Scope("singleton")` (default) — the container manages the instance |
| **C# / .NET** | `services.AddSingleton<T>()` |
| **Python** | Module-level instances (Python modules are singletons by nature) |
| **Kotlin** | `object` keyword (language-level singleton), or Koin/Hilt DI |
| **TypeScript** | Module exports (ES modules are cached after first import) |
| **Rust** | `lazy_static!` or `once_cell`/`OnceLock`, though global state is discouraged |
| **Go** | `sync.Once` + package-level variable, or DI via Wire/dig |
| **Swift** | `static let shared` pattern, or DI frameworks |

**When Singleton is still warranted:** Truly global, truly single resources (hardware
interfaces, process-level caches). Even then, wrapping it in DI improves testability.

---

## Template Method → Higher-Order Functions / Composition

Template Method uses inheritance to let subclasses fill in algorithm steps. Composition
with higher-order functions achieves the same with less coupling.

| Language | Alternative Approach |
|----------|---------------------|
| **Python** | Pass step functions as parameters, or use decorators |
| **JavaScript/TypeScript** | Pass callback functions for customizable steps |
| **Rust** | Pass closures for step customization, or trait default methods |
| **Kotlin** | Higher-order functions + lambdas |
| **Go** | Function parameters for step customization |

**When Template Method is still warranted:** When the algorithm skeleton is complex,
involves many steps, and subclass relationships are natural. Framework extension points
(lifecycle hooks) often use Template Method legitimately.

---

## Command Pattern → Closures / First-Class Functions

For simple command scenarios (no undo, no queuing), a closure suffices.

| Language | Simple Alternative |
|----------|-------------------|
| **Python** | Store a lambda/function reference; call it later |
| **JavaScript** | Store a function; callbacks and promises |
| **Rust** | `Box<dyn Fn()>` or store closures in a Vec |
| **Any language** | If you only need "execute later," a function reference works |

**When full Command pattern is still warranted:** Undo/redo, command queuing, command
logging, macro recording, transaction rollback. These require the command to carry state
(pre-execution snapshot), which a simple closure usually doesn't capture cleanly.

---

## State Pattern → Enums / Sum Types / State Machines

| Language | Native Alternative |
|----------|-------------------|
| **Rust** | Enums with `match`. The type system enforces exhaustive state handling. |
| **Kotlin** | Sealed classes + `when` |
| **Swift** | Enums with associated values |
| **TypeScript** | Discriminated unions |
| **Python** | Enum + match/case (3.10+) |
| **Java** | Sealed interfaces (Java 17+) + pattern matching (Java 21+) |
| **C / C++** | Enums + switch. State machine libraries for complex cases. |

**When the formal State pattern is still warranted:** When each state has significant,
complex behavior (not just a field value and some conditional logic). If each state is
essentially its own class worth of logic, the pattern earns its keep.

---

## General Guidance

Before reaching for a GoF pattern in its formal class-based form, ask:

1. **Does my language have a feature that provides this pattern's benefit natively?**
   If yes, use the native feature.

2. **Is a function sufficient, or do I need an object?**
   If the pattern boils down to "swap one behavior for another," a function usually works.
   If it requires state, lifecycle, or multiple coordinated methods, an object is justified.

3. **Would a developer in this language's community recognize this approach?**
   Idiomatic code is maintainable code. A Java dev expects interfaces; a Python dev
   expects duck typing and functions; a Rust dev expects traits and enums. Write for
   your audience.
