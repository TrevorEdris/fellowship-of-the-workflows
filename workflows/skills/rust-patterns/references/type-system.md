# Rust Type System

Traits, generics, associated types, PhantomData, and type-level patterns for Rust 2021 edition.

---

## Traits

Traits define shared behavior. Types implement traits to gain capabilities.

```rust
// Define a trait
pub trait Summarize {
    fn summary(&self) -> String;
    // Default implementation
    fn short_summary(&self) -> String {
        let s = self.summary();
        if s.len() > 50 { format!("{}...", &s[..50]) } else { s }
    }
}

// Implement for a type
pub struct Article {
    pub title: String,
    pub body: String,
}

impl Summarize for Article {
    fn summary(&self) -> String {
        format!("{}: {}", self.title, &self.body[..100])
    }
}
```

---

## Trait Bounds

```rust
// Single bound
fn print_summary<T: Summarize>(item: &T) {
    println!("{}", item.summary());
}

// Multiple bounds with `+`
fn process<T: Summarize + Clone + Send>(item: T) { ... }

// Where clause for readability with complex bounds
fn complex<T, U>(t: T, u: U) -> String
where
    T: Summarize + Display,
    U: Clone + Into<String>,
{ ... }

// impl Trait in parameter position (shorthand)
fn print_summary(item: &impl Summarize) {
    println!("{}", item.summary());
}

// impl Trait in return position (opaque type)
fn make_summarizable() -> impl Summarize {
    Article { title: "...".into(), body: "...".into() }
}
```

---

## Associated Types

Associated types bind a type to a trait implementation, providing a cleaner API than generic parameters.

```rust
pub trait Iterator {
    type Item;  // associated type — each impl defines what Item is
    fn next(&mut self) -> Option<Self::Item>;
}

// Generic parameter alternative — more verbose at callsites
pub trait IteratorGeneric<Item> {
    fn next(&mut self) -> Option<Item>;
}

// Constraint on associated type
fn sum_iter<I>(mut iter: I) -> i64
where
    I: Iterator<Item = i64>,
{
    let mut total = 0;
    while let Some(n) = iter.next() {
        total += n;
    }
    total
}
```

---

## Generic Structs

```rust
pub struct Cache<K, V> {
    map: HashMap<K, V>,
    capacity: usize,
}

impl<K, V> Cache<K, V>
where
    K: Eq + Hash,
{
    pub fn new(capacity: usize) -> Self {
        Self { map: HashMap::new(), capacity }
    }

    pub fn get(&self, key: &K) -> Option<&V> {
        self.map.get(key)
    }

    pub fn insert(&mut self, key: K, value: V) {
        if self.map.len() >= self.capacity {
            // eviction logic
        }
        self.map.insert(key, value);
    }
}
```

---

## PhantomData

`PhantomData<T>` carries type information at zero cost — used for state machines and marker types.

```rust
use std::marker::PhantomData;

// Type-state pattern — state encoded in the type
struct Connection<State> {
    socket: TcpStream,
    _state: PhantomData<State>,
}

struct Disconnected;
struct Connected;
struct Authenticated;

impl Connection<Disconnected> {
    pub fn new(socket: TcpStream) -> Self {
        Self { socket, _state: PhantomData }
    }

    pub fn connect(self) -> Result<Connection<Connected>, io::Error> {
        // ... perform handshake
        Ok(Connection { socket: self.socket, _state: PhantomData })
    }
}

impl Connection<Connected> {
    pub fn authenticate(self, token: &str) -> Result<Connection<Authenticated>, AuthError> {
        // ... verify token
        Ok(Connection { socket: self.socket, _state: PhantomData })
    }
}

impl Connection<Authenticated> {
    pub fn send(&mut self, data: &[u8]) -> Result<(), io::Error> {
        self.socket.write_all(data)
    }
}

// compile error: can't call .send() on Connection<Connected>
let conn = Connection::new(socket).connect()?;
conn.send(b"hello")?; // error — must authenticate first
```

---

## Dynamic Dispatch with `dyn Trait`

```rust
// Static dispatch — monomorphized at compile time, zero overhead
fn process_static<T: Summarize>(item: &T) { ... }

// Dynamic dispatch — vtable lookup at runtime, enables heterogeneous collections
fn process_dynamic(item: &dyn Summarize) { ... }

// Collection of mixed types
let items: Vec<Box<dyn Summarize>> = vec![
    Box::new(Article { ... }),
    Box::new(Tweet { ... }),
];

for item in &items {
    println!("{}", item.summary()); // dynamic dispatch
}
```

Use static dispatch by default; use `dyn Trait` when you need a heterogeneous collection or the type is not known at compile time.

---

## Common Standard Traits

| Trait | Purpose |
|-------|---------|
| `Clone` | Explicit deep copy |
| `Copy` | Implicit bitwise copy (small, stack-allocated types) |
| `Display` | User-facing string formatting |
| `Debug` | Developer-facing string formatting (derive always) |
| `From`/`Into` | Value conversion |
| `Default` | Zero/empty value construction |
| `PartialEq`/`Eq` | Equality comparison |
| `PartialOrd`/`Ord` | Ordering |
| `Hash` | Hashing (required for HashMap keys) |
| `Serialize`/`Deserialize` | Serde serialization |
