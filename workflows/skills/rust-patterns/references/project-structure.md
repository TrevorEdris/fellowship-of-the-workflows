# Rust Project Structure

Crate layout, workspace, feature flags, and Cargo configuration for Rust 2021 edition.

---

## Single Crate Layout

```
mycrate/
├── src/
│   ├── lib.rs          # Library root — public API
│   ├── main.rs         # Binary root (if binary crate)
│   ├── error.rs        # Error types (thiserror)
│   ├── store/
│   │   ├── mod.rs      # Module declaration and re-exports
│   │   ├── traits.rs   # Store trait definitions
│   │   └── postgres.rs # Postgres implementation
│   └── domain/
│       ├── mod.rs
│       └── user.rs
├── tests/
│   ├── common/
│   │   └── mod.rs      # Shared test utilities
│   └── integration_test.rs
├── benches/
│   └── throughput.rs   # Criterion benchmarks
├── Cargo.toml
└── README.md
```

---

## Workspace Layout (Multi-Crate)

```
workspace/
├── Cargo.toml          # Workspace root
├── crates/
│   ├── core/           # Shared types and traits
│   │   ├── Cargo.toml
│   │   └── src/lib.rs
│   ├── store/          # Storage implementations
│   │   ├── Cargo.toml
│   │   └── src/lib.rs
│   └── api/            # HTTP service binary
│       ├── Cargo.toml
│       └── src/main.rs
└── target/             # Shared build cache
```

```toml
# Cargo.toml (workspace root)
[workspace]
members = ["crates/*"]
resolver = "2"

[workspace.dependencies]
# Declare versions once; crates pin with { workspace = true }
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
thiserror = "1"
anyhow = "1"
```

```toml
# crates/api/Cargo.toml
[package]
name = "api"
version = "0.1.0"
edition = "2021"

[dependencies]
core = { path = "../core" }
tokio = { workspace = true }
anyhow = { workspace = true }
```

---

## Cargo.toml Best Practices

```toml
[package]
name = "myservice"
version = "0.1.0"
edition = "2021"
rust-version = "1.75"       # MSRV — enforce minimum Rust version
description = "My service"
license = "MIT"

[dependencies]
tokio = { version = "1", features = ["rt-multi-thread", "macros", "net", "time"] }
serde = { version = "1", features = ["derive"] }
sqlx = { version = "0.7", features = ["postgres", "runtime-tokio", "migrate"] }
tracing = "0.1"
anyhow = "1"
thiserror = "1"

[dev-dependencies]  # Only in tests and benchmarks
mockall = "0.12"
proptest = "1"
criterion = { version = "0.5", features = ["html_reports"] }

[profile.release]
lto = true
codegen-units = 1

[profile.dev]
opt-level = 0
debug = true
```

---

## Feature Flags

Feature flags enable optional functionality without code duplication.

```toml
[features]
default = []
postgres = ["dep:sqlx"]
redis = ["dep:redis"]
metrics = ["dep:prometheus"]

[dependencies]
sqlx = { version = "0.7", optional = true }
redis = { version = "0.25", optional = true }
prometheus = { version = "0.13", optional = true }
```

```rust
// Conditional compilation based on features
#[cfg(feature = "postgres")]
pub mod postgres_store;

#[cfg(feature = "metrics")]
fn record_metric(name: &str, value: f64) {
    prometheus::gauge!(name, value);
}
```

Build with features: `cargo build --features postgres,metrics`
Test all feature combinations: `cargo test --all-features`

---

## Module Organization

```rust
// src/lib.rs — define module tree and public API

mod error;      // private module
mod store;      // private module
mod domain;     // private module

pub use error::AppError;                   // re-export specific items
pub use domain::user::User;
pub use store::traits::{UserStore, Store}; // public interface
```

```rust
// src/store/mod.rs — internal re-exports
mod traits;
mod postgres;
mod memory;

pub use traits::{UserStore, Store};

// Only expose what consumers of this module need
#[cfg(feature = "postgres")]
pub use postgres::PostgresStore;

pub use memory::MemoryStore; // always available (no feature flag)
```

---

## `.cargo/config.toml`

```toml
# .cargo/config.toml — project-level Cargo configuration

[build]
rustflags = ["-D", "warnings"]  # Treat warnings as errors in CI

[alias]
ci = "test --all-features --all-targets"
check-all = "check --all-features --all-targets"
```

---

## Makefile / Just Commands

```makefile
.PHONY: build test lint fmt audit

build:
    cargo build --release

test:
    cargo test --all-features

test-coverage:
    cargo llvm-cov --all-features --lcov --output-path lcov.info

lint:
    cargo clippy --all-targets --all-features -- -D warnings

fmt:
    cargo fmt --all -- --check

audit:
    cargo audit
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Everything in `main.rs` or `lib.rs` | Hard to navigate, test, and maintain | Split into focused modules |
| No workspace for multi-crate projects | Duplicate dep versions, no shared `target/` | Use workspace with shared deps |
| `pub` on everything | Leaks internal types | Only `pub` what external consumers need |
| No `rust-version` in Cargo.toml | MSRV drift, unexpected breakage | Set `rust-version` and enforce in CI |
| Large `dev-dependencies` in main crate | Slow builds for library consumers | Move test-only deps to `dev-dependencies` |
