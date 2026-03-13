---
name: rust-patterns
description: Rust patterns and idioms. Use when writing, reviewing, or refactoring Rust code. Covers error handling, type system, concurrency, testing, and project structure.
---

# Rust Patterns

Authoritative reference for idiomatic Rust (2021 edition). Each reference file is self-contained and can be loaded independently.

---

## When to Use

- Writing new Rust crates, services, or libraries
- Reviewing Rust PRs for safety and correctness
- Refactoring Rust code toward idiomatic style
- Setting up a new Rust project or workspace
- Debugging Rust-specific issues (ownership, lifetimes, async, trait bounds)

---

## Quick Reference

| Topic | Reference File | Contents |
|-------|---------------|---------|
| Core idioms | `references/idiomatic-rust.md` | Ownership, borrowing, lifetimes, iterators, newtype |
| Error handling | `references/error-handling.md` | Result/Option, thiserror, anyhow, ? operator |
| Type system | `references/type-system.md` | Traits, generics, associated types, PhantomData |
| Concurrency | `references/concurrency.md` | tokio, async/await, Arc/Mutex, channels, Send/Sync |
| Testing | `references/testing.md` | Unit tests, integration tests, property-based, mocking |
| Project structure | `references/project-structure.md` | Crate layout, workspace, feature flags, Cargo |

---

## Limited Context Strategy

When context is tight, load only what you need:
- **Most tasks:** `idiomatic-rust.md` + `error-handling.md`
- **Async services:** add `concurrency.md`
- **Complex type work:** add `type-system.md`
- **Test writing:** `testing.md` only
- **New project setup:** `project-structure.md` only

---

## Overview

Rust's ownership system provides memory safety without a garbage collector. Modern idiomatic Rust means:
- Ownership-first data modeling; `Arc`/`Mutex` only when genuinely needed
- `Result`/`Option` for all fallible operations — no exceptions
- `thiserror` for library error types, `anyhow` for application code
- `tokio` for async services; standard `cargo test` for synchronous code
- Aggressive use of iterators and functional combinators over manual loops

---

## Tooling Quick Reference

| Tool | Command | Purpose |
|------|---------|---------|
| `cargo fmt` | `cargo fmt --all` | Format code (no configuration needed) |
| `cargo clippy` | `cargo clippy --all-targets -- -D warnings` | Lint (fail on warnings) |
| `cargo test` | `cargo test --all-features` | Run all tests |
| `cargo doc` | `cargo doc --no-deps --open` | Generate and view docs |
| `cargo audit` | `cargo audit` | Check for vulnerable dependencies |
| `cargo deny` | `cargo deny check` | License and dependency policy |

---

## Triggers

| Trigger | Example |
|---------|---------|
| Writing Rust code | "implement a connection pool in Rust" |
| Reviewing Rust PRs | "review this Rust service" |
| Lifetime errors | "how do I fix this lifetime error?" |
| Async design | "design an async worker pool with tokio" |
| Error handling | "how do I handle errors in a Rust library?" |
| Project setup | "set up a Rust workspace with two crates" |

---

## Key Terms

| Term | Definition |
|------|------------|
| **Ownership** | Each value has exactly one owner; when owner drops, value is freed |
| **Borrow** | Temporary access to a value without taking ownership (`&T` or `&mut T`) |
| **Lifetime** | Annotation (`'a`) that tells the compiler how long a reference must remain valid |
| **Trait** | Rust's interface system — defines shared behavior types can implement |
| **`Send`** | Marker trait: type can be transferred across thread boundaries |
| **`Sync`** | Marker trait: type can be shared between threads via `&T` |
| **`Pin`** | Prevents a value from being moved in memory (required for self-referential async futures) |
| **`?` operator** | Early-return shorthand for `Result`/`Option` — equivalent to `return Err(e.into())` |
