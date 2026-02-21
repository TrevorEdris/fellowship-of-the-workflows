# Rust Testing

Unit tests, integration tests, async tests, property-based testing, and mocking for Rust 2021 edition.

---

## Unit Tests

Unit tests live in the same file as the code they test, in a `#[cfg(test)]` module.

```rust
// src/parse.rs
pub fn parse_port(s: &str) -> Result<u16, std::num::ParseIntError> {
    s.parse()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_port() {
        assert_eq!(parse_port("8080").unwrap(), 8080);
    }

    #[test]
    fn port_zero() {
        assert_eq!(parse_port("0").unwrap(), 0);
    }

    #[test]
    fn empty_string_errors() {
        assert!(parse_port("").is_err());
    }

    #[test]
    fn non_numeric_errors() {
        assert!(parse_port("abc").is_err());
    }

    #[test]
    #[should_panic(expected = "explicit panic")]
    fn panics_as_expected() {
        panic!("explicit panic");
    }
}
```

---

## Integration Tests

Integration tests live in `tests/` and test the public API of the crate.

```rust
// tests/store_test.rs
use mylib::store::{MemoryStore, Store};

#[test]
fn insert_and_retrieve() {
    let mut store = MemoryStore::new();
    store.insert("key".into(), "value".into());
    assert_eq!(store.get("key"), Some(&"value".to_string()));
}

#[test]
fn missing_key_returns_none() {
    let store = MemoryStore::new();
    assert!(store.get("nonexistent").is_none());
}
```

---

## Async Tests with tokio

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn fetches_user() {
        let client = FakeHttpClient::new();
        client.stub_get("/users/u1", 200, r#"{"id":"u1","email":"alice@example.com"}"#);

        let repo = UserRepository::new(client);
        let user = repo.get_user("u1").await.unwrap();
        assert_eq!(user.email, "alice@example.com");
    }

    #[tokio::test]
    async fn returns_not_found() {
        let client = FakeHttpClient::new();
        client.stub_get("/users/u1", 404, "");

        let repo = UserRepository::new(client);
        let err = repo.get_user("u1").await.unwrap_err();
        assert!(matches!(err, StoreError::NotFound { .. }));
    }
}
```

---

## Test Helpers and Fixtures

```rust
// tests/common/mod.rs
pub struct TestDb {
    pub pool: sqlx::PgPool,
    pub name: String,
}

impl TestDb {
    pub async fn new() -> Self {
        let name = format!("test_{}", uuid::Uuid::new_v4().simple());
        let pool = create_db(&name).await.expect("create test db");
        sqlx::migrate!("./migrations").run(&pool).await.expect("migrate");
        Self { pool, name }
    }
}

impl Drop for TestDb {
    fn drop(&mut self) {
        // Schedule async cleanup — sync Drop limitation
        let name = self.name.clone();
        std::thread::spawn(move || {
            tokio::runtime::Runtime::new()
                .unwrap()
                .block_on(drop_db(&name));
        });
    }
}
```

---

## Property-Based Testing with proptest

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn encode_decode_roundtrip(s in "\\PC*") {
        let encoded = encode(&s);
        let decoded = decode(&encoded).unwrap();
        prop_assert_eq!(s, decoded);
    }

    #[test]
    fn parse_any_valid_json_number(n in i32::MIN..=i32::MAX) {
        let s = n.to_string();
        let parsed: i32 = s.parse().unwrap();
        prop_assert_eq!(n, parsed);
    }
}
```

---

## Mocking with mockall

```rust
use mockall::automock;

#[automock]
pub trait UserStore {
    fn get_user(&self, id: &str) -> Result<User, StoreError>;
    fn save_user(&mut self, user: &User) -> Result<(), StoreError>;
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;

    #[test]
    fn handler_returns_user() {
        let mut store = MockUserStore::new();
        store
            .expect_get_user()
            .with(eq("u1"))
            .times(1)
            .returning(|_| Ok(User { id: "u1".into(), email: "alice@example.com".into() }));

        let handler = UserHandler::new(store);
        let result = handler.get("u1").unwrap();
        assert_eq!(result.email, "alice@example.com");
    }
}
```

---

## Test Organization

```
src/
├── lib.rs          # #[cfg(test)] unit tests inline
└── store.rs        # #[cfg(test)] mod tests { ... }

tests/
├── common/
│   └── mod.rs      # Shared fixtures and helpers
├── store_test.rs   # Integration tests for store module
└── api_test.rs     # End-to-end HTTP tests
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `unwrap()` in test code without explanation | Hides failure location | Use `expect("context")` or `assert!(result.is_ok())` |
| Global mutable state in tests | Test interference | Use per-test setup with `TestDb` or local state |
| Skipping async tests with `block_on` manually | Misses tokio runtime context | Use `#[tokio::test]` |
| No `#[cfg(test)]` on test helpers | Included in release binary | Always gate with `#[cfg(test)]` |
| `assert_eq!(a, b)` reversed args | Confusing failure messages | Convention: `assert_eq!(expected, actual)` |
