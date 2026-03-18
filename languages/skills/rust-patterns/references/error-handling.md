# Rust Error Handling

Result, Option, thiserror, anyhow, and the `?` operator for Rust 2021 edition.

---

## Core Principle

Errors are values in Rust. All fallible operations return `Result<T, E>` or `Option<T>`. There are no exceptions.

```rust
// Result — operation that can fail with a typed error
fn parse_port(s: &str) -> Result<u16, std::num::ParseIntError> {
    s.parse::<u16>()
}

// Option — value that may or may not be present
fn find_user(id: &str) -> Option<User> {
    users.get(id).cloned()
}
```

---

## The `?` Operator

`?` is early-return shorthand. On `Err(e)`, it returns `Err(e.into())` from the current function.

```rust
use std::fs;
use std::io;

fn read_config(path: &str) -> Result<Config, io::Error> {
    let contents = fs::read_to_string(path)?; // returns Err on failure
    let config: Config = serde_json::from_str(&contents)?;
    Ok(config)
}
```

For `?` to work across error types, implement `From<SrcError> for DstError` or use `anyhow`.

---

## thiserror (Library Error Types)

Use `thiserror` to define structured error enums in libraries. Callers can match on variants.

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum StoreError {
    #[error("record {id} not found in {collection}")]
    NotFound { collection: String, id: String },

    #[error("duplicate key {key}")]
    Conflict { key: String },

    #[error("database error")]
    Db(#[from] sqlx::Error), // auto From<sqlx::Error> impl
}

// Usage
pub fn get_user(id: &str) -> Result<User, StoreError> {
    users.get(id).ok_or_else(|| StoreError::NotFound {
        collection: "users".into(),
        id: id.to_string(),
    })
}
```

Library crates should **never** use `anyhow` as a return type — it erases the error type.

---

## anyhow (Application Error Handling)

Use `anyhow` in binary crates and application code where error details don't need to be matched.

```rust
use anyhow::{Context, Result};

fn load_and_process(path: &str) -> Result<Report> {
    let config = load_config(path)
        .with_context(|| format!("loading config from {path}"))?;

    let data = fetch_data(&config.endpoint)
        .context("fetching remote data")?;

    Ok(process(data))
}
```

`Context::context` and `with_context` add human-readable context to the error chain.

---

## Option Methods

```rust
let opt: Option<i32> = Some(42);

// Transform the value if Some
opt.map(|x| x * 2);           // Some(84)

// Chain Options
opt.and_then(|x| if x > 0 { Some(x) } else { None });

// Provide a default
opt.unwrap_or(0);              // 42 (or 0 if None)
opt.unwrap_or_else(|| compute_default());

// Convert to Result
opt.ok_or(StoreError::NotFound { ... })?;

// Filter
opt.filter(|&x| x > 10);      // Some(42)
opt.filter(|&x| x > 100);     // None
```

---

## Result Methods

```rust
let res: Result<i32, String> = Ok(42);

// Transform the Ok value
res.map(|x| x * 2);           // Ok(84)

// Transform the Err value
res.map_err(|e| format!("error: {e}"));

// Chain Results
res.and_then(|x| if x > 0 { Ok(x) } else { Err("negative".into()) });

// Provide a default on error
res.unwrap_or(0);
res.unwrap_or_else(|_| default_value());

// Log and continue
if let Err(e) = optional_operation() {
    tracing::warn!("skipping: {e}");
}
```

---

## Error Conversion with `From`

```rust
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("store error: {0}")]
    Store(#[from] StoreError),  // #[from] generates From<StoreError> for AppError

    #[error("validation: {0}")]
    Validation(String),
}

fn handler(id: &str) -> Result<User, AppError> {
    let user = store.get_user(id)?; // StoreError -> AppError via From
    Ok(user)
}
```

---

## When to Panic

Panics are for programmer errors — invariants that should never be violated at runtime. They are appropriate in:

```rust
// Index with known-valid bounds (document why)
let first = items[0]; // panics if empty — caller must ensure non-empty

// Initialization that must succeed at startup
let config = Config::from_env().expect("MYAPP_CONFIG must be set at startup");

// Tests
assert_eq!(result, expected);
```

**Never** use `unwrap()`/`expect()` in request-handling code paths.

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `.unwrap()` in production code | Panics at runtime | Use `?`, `.ok_or()`, or `match` |
| `Box<dyn Error>` as library return type | Erases error variant info | Return `YourError` enum with `thiserror` |
| Ignoring `Result` with `let _ = ...` | Silent error discard | Handle or log the error |
| `anyhow` in library APIs | Can't match on errors | Use typed errors in libraries |
| Nesting `match` deeply on Result/Option | Unreadable | Use `?`, `.map()`, `.and_then()` |
