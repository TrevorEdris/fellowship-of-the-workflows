# Behavioral Patterns Reference

Behavioral patterns are concerned with algorithms and the assignment of responsibilities
between objects. They describe not just patterns of classes or objects, but the patterns
of communication between them.

The core question: **How should these objects talk to each other, and who is responsible
for what?**

---

## Chain of Responsibility

**Purpose:** Decouple the sender of a request from its receiver by giving multiple objects
a chance to handle the request. Chain the receiving objects and pass the request along
until an object handles it.

**When to use:**
- Multiple objects may handle a request, and the handler isn't known in advance
- You want to issue a request without specifying the receiver explicitly
- The set of handlers should be configurable dynamically (add/remove handlers at runtime)
- Classic examples: middleware pipelines, event bubbling, logging level handlers, approval
  chains (manager → director → VP)

**When NOT to use:**
- Every request MUST be handled. Chain of Responsibility can silently drop requests if
  no handler matches. If this is unacceptable, add a guaranteed terminal handler or use
  a different pattern.
- The "chain" is really just one handler with conditional logic. An if/else or switch
  is simpler than a chain of one.
- Handler ordering is critical and fragile. If reordering the chain breaks things in
  non-obvious ways, the chain abstraction is hiding important dependencies.

**Common misapplications:**
- Chains where every handler always passes to the next (they're not handling, just
  observing — that's middleware or Observer, not Chain of Responsibility).
- Extremely long chains where debugging "which handler ate my request?" becomes painful.

**Costs:** Can be hard to debug (which handler processed this?). No guarantee a request
will be handled. Performance overhead of traversing the chain.

---

## Command

**Purpose:** Encapsulate a request as an object, thereby letting you parameterize clients
with different requests, queue or log requests, and support undoable operations.

**When to use:**
- You need **undo/redo** functionality (each command stores enough state to reverse itself)
- You need to queue, schedule, or log operations
- You want to decouple the invoker of an operation from the object that performs it
- You need to support macro commands (composite commands that execute a sequence)
- Transaction-like behavior where operations need to be batched and committed/rolled back

**When NOT to use:**
- The operation is simple and doesn't need undo, queuing, or logging. Wrapping a simple
  method call in a Command object adds overhead for no benefit.
- There's no invoker/receiver decoupling needed. If the caller always knows exactly what
  to call, Command is indirection without purpose.
- Your language has first-class functions. In Python, JS, or Kotlin, a closure or lambda
  often serves the same purpose as a Command object without the boilerplate.

**Common misapplications:**
- Command objects that are just method wrappers with no state (no undo capability, no
  queuing). This is the Command pattern without its actual benefits.
- Not implementing undo properly. If commands mutate state but don't capture enough
  pre-state to reverse it, undo will be buggy or incomplete.

**Costs:** One class per command type. Can lead to a proliferation of small classes.
Undo logic can be complex, especially when commands have interdependencies.

---

## Iterator

**Purpose:** Provide a way to access elements of a collection sequentially without
exposing its underlying representation.

**When to use:**
- You need to traverse a custom data structure (tree, graph, linked structure) with a
  standard iteration interface
- You need multiple simultaneous traversals of the same collection
- You want to provide a uniform traversal interface across different collection types

**When NOT to use:**
- Your language already provides iteration protocols (Python's `__iter__`, Java's
  `Iterable`, Rust's `Iterator` trait, C++'s iterator concept). In modern languages,
  you almost never implement the GoF Iterator pattern from scratch — you implement the
  language's iteration protocol instead.
- The collection is a simple list/array. Every modern language iterates these natively.

**Language note:** This is one of the GoF patterns most thoroughly absorbed by modern
languages. In 2025, "implement the Iterator pattern" almost always means "implement your
language's iterator protocol," not "create an Iterator interface with hasNext() and next()."

**Costs:** Minimal when using language-native protocols. Can be complex for custom data
structures with multiple traversal strategies.

---

## Mediator

**Purpose:** Define an object that encapsulates how a set of objects interact. Promotes
loose coupling by keeping objects from referring to each other explicitly.

**When to use:**
- Multiple objects communicate in complex ways, creating a tangled web of dependencies
- You want to centralize communication logic so that objects only know about the mediator,
  not about each other
- Classic examples: chat rooms (users communicate through the room, not directly),
  UI form coordination (widgets notify a controller, which updates other widgets), air
  traffic control

**When NOT to use:**
- Only two objects need to communicate. Mediator is for N-to-N communication; for 1-to-1,
  just have them talk directly or use Observer.
- The mediator becomes a God Object that contains all the business logic. The mediator
  should coordinate, not compute.
- The communication patterns are simple and unlikely to change.

**Common misapplications:**
- Mediator that grows to contain all application logic, becoming a central controller
  that everything depends on (worse than the original coupling).
- Using Mediator when Observer would suffice (Mediator is for coordinated interaction;
  Observer is for one-way notification).

**Costs:** The mediator can become a monolith. All communication logic concentrates in one
place, which can be a maintenance bottleneck.

---

## Memento

**Purpose:** Capture and externalize an object's internal state so that the object can be
restored to this state later, without violating encapsulation.

**When to use:**
- You need **snapshot/restore** functionality (undo, checkpoints, save/load game state)
- The internal state must be saved without exposing the object's implementation details
- Direct serialization would expose too much or couple consumers to internal structure

**When NOT to use:**
- The state is trivially small and easy to copy. Just copy the fields directly.
- The state is enormous and snapshots would consume too much memory. Consider incremental
  changes (Command pattern with undo) instead.
- The object's state is already public / the object is a DTO. No encapsulation to protect.

**Common misapplications:**
- Storing references to mutable objects in the memento without deep copying. The memento
  then mutates when the original does, defeating the purpose.
- Creating mementos too frequently (every keystroke) without any cleanup strategy.

**Costs:** Memory consumption for stored mementos. Deep copy complexity. Lifecycle
management (when to discard old mementos).

---

## Observer

**Purpose:** Define a one-to-many dependency between objects so that when one object
changes state, all its dependents are notified and updated automatically.

**When to use:**
- One object's state change should trigger reactions in other objects, but you don't want
  tight coupling between them
- The set of objects that need to react can change dynamically
- Classic examples: event systems, UI data binding, pub/sub messaging, reactive streams

**When NOT to use:**
- There's only one observer and it will never change. Direct method calls are simpler.
- The notification order matters and must be guaranteed. Observer doesn't typically
  guarantee order.
- Observers trigger further state changes that trigger further notifications, creating
  cascade / infinite loop risks. This is the most dangerous pitfall of Observer.

**Common misapplications:**
- Notification cascades: Observer A changes state in response to Subject, which triggers
  Observer B, which changes state on Subject, which notifies A again... infinite loop.
- Memory leaks from forgotten subscriptions (observers that are never unregistered).
- Using Observer for synchronous communication when events should be asynchronous.

**Language note:** Most modern frameworks provide reactive/event systems that implement
Observer natively (React state, Vue reactivity, RxJS, Kotlin Flow, C# events). Use the
framework's mechanism rather than implementing raw Observer.

**Costs:** Can make control flow hard to follow (who's reacting to what?). Memory leaks
from unregistered observers. Cascade risks. Debugging event-driven systems is notoriously
difficult.

---

## State

**Purpose:** Allow an object to alter its behavior when its internal state changes. The
object will appear to change its class.

**When to use:**
- An object's behavior depends on its state, and it must change behavior at runtime
  depending on that state
- Operations have large conditional statements that depend on the object's state
  (many if/else or switch blocks checking the same state variable)
- You're modeling a finite state machine with well-defined transitions
- Classic examples: TCP connection states, document workflow (draft → review → published),
  game character states (idle → running → jumping → falling)

**When NOT to use:**
- There are only 2-3 states with trivial transitions. An enum and a switch statement
  is simpler and more readable.
- State transitions are complex and need to be visible at a glance. The State pattern
  distributes transition logic across multiple classes, which can make the overall state
  machine harder to understand. A state transition table might be clearer.
- States don't actually have different behavior — they just have different data.

**Common misapplications:**
- States that know too much about each other (tight coupling between state classes).
  Transitions should ideally go through the context, not directly between states.
- Forgetting to define what happens for EVERY event in EVERY state. Incomplete state
  machines are a bug factory.

**Costs:** One class per state. Transition logic can be spread across many files, making
the overall state machine hard to reason about. Consider if a state machine library
provides better tooling.

---

## Strategy

**Purpose:** Define a family of algorithms, encapsulate each one, and make them
interchangeable. Lets the algorithm vary independently from clients that use it.

**When to use:**
- You need to switch between different algorithms at runtime (sorting strategies,
  compression algorithms, validation rules, pricing strategies)
- A class has multiple behaviors that appear as conditional statements
  (if/else or switch on a "type" field)
- You want to isolate the algorithm's implementation details from the code that uses it

**When NOT to use:**
- There's only one algorithm and no realistic prospect of adding more. A strategy
  interface with one implementation is a needless abstraction.
- Your language has first-class functions. In Python, JS, Rust, Go, Kotlin, etc., passing
  a function/closure IS the Strategy pattern, just without the ceremony of an interface +
  implementation class. Don't create a `SortStrategy` interface in Python — pass a
  key function.
- The "strategies" share significant logic. Template Method might be more appropriate
  when the algorithm skeleton is fixed and only steps vary.

**Language note:** This is the GoF pattern most completely replaced by first-class
functions in modern languages. If the strategy is a single method, use a function. If it's
a cluster of related methods that must be swapped together, the interface-based pattern
still has value.

**Costs:** Clients must be aware that different strategies exist. Strategy objects can
proliferate. In languages with first-class functions, the pattern is essentially free.

---

## Template Method

**Purpose:** Define the skeleton of an algorithm in a base class, letting subclasses
override specific steps without changing the algorithm's structure.

**When to use:**
- Multiple classes share the same algorithm structure but differ in specific steps
- You want to control which parts of an algorithm subclasses can customize (the
  "Hollywood Principle": don't call us, we'll call you)
- Framework hooks (beforeSave, afterLoad, onValidate)

**When NOT to use:**
- The algorithm steps are all different — no shared skeleton. If there's no common
  structure, there's no template.
- You need to swap algorithms at runtime. Template Method uses inheritance, which is
  fixed at compile time. Use Strategy for runtime swapping.
- Deep inheritance hierarchies. Template Method encourages inheritance, which can lead
  to fragile hierarchies if overused.

**Common misapplications:**
- Template Methods with too many hook points, making the actual flow incomprehensible.
- Using inheritance (Template Method) when composition (Strategy) would be more flexible.
  In modern OOP, composition is generally preferred over inheritance.

**Costs:** Relies on inheritance, which creates tighter coupling than composition-based
alternatives. Subclasses are locked to the template's structure.

---

## Visitor

**Purpose:** Represent an operation to be performed on the elements of an object structure.
Visitor lets you define new operations without changing the classes of the elements on which
it operates.

**When to use:**
- You need to perform many distinct and unrelated operations on objects in a structure,
  and you don't want to "pollute" those classes with all these operations
- The class hierarchy of objects is stable (new types are rare), but new operations are
  frequent
- You need to accumulate state across a complex structure during traversal (e.g., code
  analysis, rendering, serialization)

**When NOT to use:**
- The object hierarchy changes frequently. Adding a new element type requires updating
  EVERY visitor. This is the fundamental tradeoff: Visitor makes it easy to add
  operations but hard to add types. If types change often, Visitor is the wrong choice.
- Your language has pattern matching (Rust match, Scala match, C# switch expressions
  with patterns, Python match/case 3.10+). Pattern matching often provides Visitor's
  benefits with less ceremony.
- The operations are simple enough to live on the classes themselves.

**Language note:** Visitor is largely unnecessary in languages with algebraic data types
and pattern matching (Rust, F#, Scala, Haskell, modern C#, Python 3.10+).

**Costs:** Breaks encapsulation (visitors must know the internal structure of elements).
Adding a new element type is expensive (every visitor must be updated). Can be hard to
understand for developers unfamiliar with the double-dispatch mechanism.
