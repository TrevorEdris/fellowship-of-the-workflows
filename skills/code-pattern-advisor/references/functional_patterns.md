# Functional Patterns Reference

These patterns come from functional programming and address error handling, null safety,
and composition of fallible or effectful operations. They have crossed into mainstream
OOP languages via types like Optional/Maybe, Result/Either, and reactive streams.

The core question: **How do I chain operations that might fail, produce nothing, or have
side effects, without tangling my logic in error-checking boilerplate?**

These patterns are not alternatives to OOP patterns — they complement them. A Repository
can return a Result<Entity, NotFoundError> instead of throwing an exception. A Strategy
can be a function rather than an interface.

---

## Result / Either

**Purpose:** Represent the outcome of an operation that can succeed or fail, as a value
rather than an exception. `Result<T, E>` (or `Either<L, R>`) holds either a success value
or an error value, forcing the caller to handle both cases explicitly.

**When to use:**
- Errors are expected, recoverable, and part of normal control flow (validation failures,
  not-found conditions, permission denied, parsing errors)
- You want to make failure explicit in the function's return type so callers can't ignore
  it
- You're chaining multiple fallible operations and want to short-circuit on the first
  failure without nested try/catch blocks
- You want to avoid exceptions for flow control (exceptions should be exceptional)

**When NOT to use:**
- Errors are truly exceptional and unrecoverable (out of memory, stack overflow,
  corrupted state). Let these throw/panic.
- The language's exception handling is idiomatic and the team is comfortable with it.
  Don't force Result types onto a Java codebase that uses checked exceptions by convention
  unless the team agrees.
- Every function returns Result, even when failure is impossible. This adds wrapping and
  unwrapping noise to code that can't actually fail.
- Errors need stack traces for debugging. Result types typically don't capture stack
  traces — if you need them, exceptions are better.

**Common misapplications:**
- Wrapping exceptions in Result at every boundary, creating Result<Result<T, E1>, E2>
  nesting nightmares. Use `.flatMap()` / `.andThen()` to flatten.
- Ignoring the error case by calling `.unwrap()` / `.get()` everywhere, defeating the
  purpose of explicit error handling.
- Result types with overly broad error types (`Result<User, String>` where the error is
  just a message). Use specific error types or enums.

**Language availability:**
- **Rust**: `Result<T, E>` — native, idiomatic, essential
- **Kotlin**: `Result<T>` or Arrow's `Either<L, R>`
- **TypeScript**: `Result<T, E>` via libraries (fp-ts, neverthrow)
- **Java**: `Either<L, R>` via Vavr; or simpler sealed class approach
- **Swift**: `Result<Success, Failure>`
- **C++**: `std::expected<T, E>` (C++23), `tl::expected` before that
- **Python**: Returns library, or manual with union types
- **Go**: Multiple return values (error, value) serve a similar purpose idiomatically
- **C#**: `OneOf<T, TError>` or custom discriminated unions; or just use exceptions

**Costs:** Unfamiliar to developers from exception-heavy backgrounds. Can make simple code
verbose if the language lacks syntactic sugar (`?` operator in Rust, `do` notation in
Haskell). Must define error types carefully.

---

## Option / Maybe

**Purpose:** Represent the presence or absence of a value without using null. Forces the
caller to explicitly handle the "nothing" case.

**When to use:**
- A function may legitimately return "nothing" (lookup by ID that might not exist,
  first element of a potentially empty list, optional configuration values)
- You want to eliminate null pointer exceptions at the type level
- You're chaining operations where any step might produce nothing, and you want to
  short-circuit cleanly

**When NOT to use:**
- The value should always be present. If absence indicates a bug, use an assertion or
  throw — don't silently swallow the error into a None.
- You need to know WHY there's no value. Option/Maybe only says "present or absent."
  If you need an error reason, use Result/Either instead.
- The language doesn't distinguish Option<T> from T at the type level (dynamically typed
  languages). In Python, `Optional[str]` exists but isn't enforced at runtime — its value
  depends on team discipline and static analysis tooling.
- The language has null safety built in (Kotlin's `?` nullable types, C#'s nullable
  reference types). These provide Option semantics without a wrapper type.

**Common misapplications:**
- `Option<Option<T>>` — double-wrapping usually indicates a design problem.
- Using Option where null is the idiomatic language choice and the team/tooling is
  comfortable with null safety (Kotlin, modern C#).
- `.unwrap()` / `.get()` everywhere — if you're always unwrapping, you're not getting
  the safety benefit.

**Language availability:**
- **Rust**: `Option<T>` — native, pervasive, essential
- **Java**: `Optional<T>` — standard but controversial in its API design
- **Swift**: `Optional<T>` (the `?` syntax) — native and idiomatic
- **Kotlin**: Nullable types `T?` — fulfills the same role natively
- **Haskell/F#/Scala**: `Maybe` / `Option` — core type
- **C++**: `std::optional<T>` (C++17)
- **Python**: `Optional[T]` type hint, but no runtime enforcement
- **TypeScript**: `T | undefined` or `T | null` with strict null checks

**Costs:** Wrapping/unwrapping verbosity (mitigated by language features like `?`, pattern
matching, `map`/`flatMap`). Potential for double-wrapping. Learning curve for teams
unfamiliar with the concept.

---

## Railway-Oriented Programming

**Purpose:** A metaphor and composition strategy for chaining multiple fallible operations.
Think of a two-track railway: the happy path (success track) and the error path (failure
track). Each operation either continues on the success track or shunts to the error track.
Once on the error track, subsequent operations are bypassed.

**When to use:**
- You have a pipeline of validation/transformation steps where each can fail
- You want a clean, linear expression of a multi-step process without deeply nested
  if/else or try/catch blocks
- Classic examples: form validation pipelines, API request processing (parse → validate →
  authorize → execute → respond), ETL pipelines

**When NOT to use:**
- The pipeline isn't linear — branches, loops, or parallel paths make the railway metaphor
  misleading.
- Error recovery is needed mid-pipeline (early steps fail but later steps can compensate).
  Railway assumes "first failure stops everything."
- The pipeline has only 1-2 steps. The overhead of setting up the railway isn't justified.
- The team isn't comfortable with functional composition. Forcing railway-oriented code on
  a team that thinks imperatively will reduce readability, not improve it.

**Implementation approaches:**
- **Rust**: Chain `Result` with `?` operator (the language essentially gives you ROP
  for free)
- **F# / Haskell**: `bind` / `>>=` / computation expressions
- **TypeScript**: fp-ts `pipe` + `Either` chain, or neverthrow
- **Java**: Vavr's `Either` with `.flatMap()` chains
- **Python**: Returns library, or manual with early returns and Result types
- **Any language**: Can be approximated with early returns (`if err != nil { return err }`)

**Common misapplications:**
- Applying railway to every function, even trivial ones that can't fail. Not everything
  needs two tracks.
- Overly long pipelines where a failure in step 1 produces an error message that doesn't
  make sense by step 15. Error context can be lost in long chains.
- Using railway-oriented programming as an excuse to never use exceptions, even for truly
  exceptional cases.

**Costs:** Unfamiliar paradigm for many developers. Can make debugging harder (where in
the pipeline did it fail?). Error types must be carefully designed to carry enough context.

---

## Monad (General Concept)

**Purpose:** A design pattern for chaining computations that carry additional context
(failure, optionality, asynchrony, state, logging, etc.) while keeping the core logic
clean.

This entry exists for conceptual completeness. In practice, you rarely "implement a monad"
— you use specific monads (Result, Option, Future/Promise, List) that your language
provides.

**The practical essence:** If a type has `map` (apply a function to the inner value) and
`flatMap` (apply a function that returns the same wrapper type, and flatten), and those
operations obey associativity and identity laws, it's a monad. You don't need to know the
math to use them.

**When to recognize monadic thinking is relevant:**
- You're calling `.map()` and `.flatMap()` (or `.then()` on Promises) — you're already
  using monads
- You're nesting wrapper types (`Optional<Optional<T>>`, `Promise<Promise<T>>`) — you
  probably need `.flatMap()` instead of `.map()`
- You have repeated patterns of "unwrap, do something, re-wrap" — a monadic chain can
  eliminate this boilerplate

**When NOT to invoke monadic thinking:**
- As jargon to make simple code sound sophisticated. "We use the Maybe monad" is no
  better than "we use Optional" if the usage is identical.
- When the team doesn't share the vocabulary. Using monad terminology in a codebase
  where nobody knows what it means reduces readability.
- In languages where the concept doesn't translate naturally (Go, C). Not every language
  benefits from monadic abstractions.

**Costs:** High jargon barrier. The concept is simple but the mathematical framing scares
people. In many languages, you get monadic benefits through language features (Rust's `?`,
Kotlin's `?.`, async/await) without ever using the word "monad."
