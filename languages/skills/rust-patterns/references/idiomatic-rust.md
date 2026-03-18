# Idiomatic Rust

Ownership, borrowing, lifetimes, iterators, and core idioms for Rust 2021 edition.

---

## Ownership Rules

1. Each value has exactly one owner.
2. When the owner goes out of scope, the value is dropped (memory freed).
3. There can be any number of immutable borrows (`&T`) OR exactly one mutable borrow (`&mut T`) — not both simultaneously.

```rust
fn main() {
    let s = String::from("hello");
    let s2 = s;           // s is moved; s is no longer valid
    // println!("{}", s); // compile error: value moved
    println!("{}", s2);   // ok
}

// Borrow instead of move
fn print_len(s: &str) {
    println!("{}", s.len());
}

let s = String::from("hello");
print_len(&s); // borrow
println!("{}", s); // s still valid
```

---

## Cloning

Clone only when you need an independent copy. Cloning is explicit and visible in the source.

```rust
// Cheap types that implement Copy are copied implicitly
let x: i32 = 42;
let y = x; // copy — x and y are independent

// Heap types require explicit clone
let s1 = String::from("hello");
let s2 = s1.clone(); // explicit allocation
println!("{} {}", s1, s2); // both valid
```

Excessive `.clone()` is a code smell indicating an ownership design issue.

---

## Iterators

Prefer iterators over manual index-based loops. They compile to equivalent or better machine code.

```rust
// Sum of squares of even numbers
let result: i32 = (0..100)
    .filter(|&x| x % 2 == 0)
    .map(|x| x * x)
    .sum();

// Collect into a Vec
let names: Vec<String> = users
    .iter()
    .filter(|u| u.active)
    .map(|u| u.name.clone())
    .collect();

// Find first match
let admin = users.iter().find(|u| u.role == Role::Admin);

// Check any/all
let has_admin = users.iter().any(|u| u.role == Role::Admin);
```

---

## Pattern Matching

Use `match`, `if let`, and `while let` to destructure and branch on values.

```rust
// Match on enum variants
match status {
    Status::Active   => process(),
    Status::Pending  => enqueue(),
    Status::Closed   => return,
}

// if let for single-variant handling
if let Some(user) = find_user(id) {
    greet(&user);
}

// while let for iterator-like draining
while let Some(item) = queue.pop() {
    handle(item);
}

// Destructuring in function params
fn handle_point(&(x, y): &(i32, i32)) {
    println!("({x}, {y})");
}
```

---

## Newtype Pattern

Wrap primitives to create distinct types with domain meaning.

```rust
struct UserId(String);
struct OrderId(String);
struct AmountCents(i64);

impl UserId {
    pub fn new(s: impl Into<String>) -> Self {
        Self(s.into())
    }
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

// Mixing UserId and OrderId is now a compile error
fn get_user(id: UserId) -> User { ... }
let order_id = OrderId::new("o123");
get_user(order_id); // compile error: expected UserId, found OrderId
```

---

## Builder Pattern

For structs with many optional fields, use a builder to enforce initialization order.

```rust
pub struct ServerConfig {
    pub addr: String,
    pub timeout: Duration,
    pub tls: Option<TlsConfig>,
}

pub struct ServerConfigBuilder {
    addr: String,
    timeout: Duration,
    tls: Option<TlsConfig>,
}

impl ServerConfigBuilder {
    pub fn new(addr: impl Into<String>) -> Self {
        Self {
            addr: addr.into(),
            timeout: Duration::from_secs(30),
            tls: None,
        }
    }

    pub fn timeout(mut self, d: Duration) -> Self {
        self.timeout = d;
        self
    }

    pub fn tls(mut self, cfg: TlsConfig) -> Self {
        self.tls = Some(cfg);
        self
    }

    pub fn build(self) -> ServerConfig {
        ServerConfig { addr: self.addr, timeout: self.timeout, tls: self.tls }
    }
}

let cfg = ServerConfigBuilder::new("0.0.0.0:8080")
    .timeout(Duration::from_secs(10))
    .build();
```

---

## Lifetimes

Lifetimes prevent dangling references. The compiler infers most lifetimes; annotate only when it cannot.

```rust
// Lifetime annotation: output lives as long as the shorter-lived input
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Struct holding a reference must declare a lifetime
struct Parser<'a> {
    input: &'a str,
    pos: usize,
}

impl<'a> Parser<'a> {
    fn next_token(&mut self) -> &'a str {
        // ... returns a slice of self.input
    }
}
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `.clone()` everywhere | Masks ownership design flaws | Refactor borrows; clone only at boundaries |
| `unwrap()` in production | Panics on `None`/`Err` | Use `?`, `.ok_or()`, or `match` |
| Returning `Box<dyn Error>` from libraries | Erases error type info | Return a concrete error enum (`thiserror`) |
| `unsafe` without a comment | Invariant unclear | Document every `unsafe` block |
| Index loops `for i in 0..v.len()` | Verbose, panics on out-of-bounds | Use `for item in &v` or `.iter().enumerate()` |
