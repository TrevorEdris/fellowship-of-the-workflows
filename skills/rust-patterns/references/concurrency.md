# Rust Concurrency

tokio, async/await, Arc/Mutex, channels, Send/Sync, and safe concurrent patterns for Rust 2021 edition.

---

## async/await with tokio

```rust
use tokio::time::{sleep, Duration};
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let result = fetch_user("u1").await?;
    println!("{:?}", result);
    Ok(())
}

async fn fetch_user(id: &str) -> Result<User> {
    let resp = reqwest::get(format!("https://api.example.com/users/{id}"))
        .await?
        .error_for_status()?
        .json::<User>()
        .await?;
    Ok(resp)
}
```

**Key rule:** `async fn` returns a `Future` — it does nothing until `.await`ed or spawned.

---

## Spawning Tasks

```rust
use tokio::task::JoinHandle;

// Spawn a task — runs concurrently with the current task
let handle: JoinHandle<Result<User>> = tokio::spawn(async move {
    fetch_user(id).await
});

// Await the result
let user = handle.await??; // outer ? for JoinError, inner ? for Result<User>
```

Spawned tasks must be `'static + Send`. If a task panics, `JoinHandle::await` returns `Err(JoinError)`.

---

## JoinSet for Multiple Tasks

```rust
use tokio::task::JoinSet;

async fn fetch_all(ids: Vec<String>) -> Vec<Result<User>> {
    let mut set = JoinSet::new();

    for id in ids {
        set.spawn(async move { fetch_user(&id).await });
    }

    let mut results = Vec::new();
    while let Some(res) = set.join_next().await {
        results.push(res.expect("task panicked"));
    }
    results
}
```

---

## Shared State: Arc and Mutex

`Arc<T>` enables shared ownership across threads. `Mutex<T>` provides interior mutability.

```rust
use std::sync::{Arc, Mutex};

#[derive(Clone)]
struct AppState {
    counter: Arc<Mutex<u64>>,
    cache: Arc<tokio::sync::RwLock<HashMap<String, User>>>,
}

impl AppState {
    async fn increment(&self) {
        let mut c = self.counter.lock().unwrap();
        *c += 1;
    }

    async fn get_user(&self, id: &str) -> Option<User> {
        self.cache.read().await.get(id).cloned()
    }

    async fn set_user(&self, id: String, user: User) {
        self.cache.write().await.insert(id, user);
    }
}
```

**Lock rules:**
- Use `tokio::sync::Mutex` (not `std::sync::Mutex`) when the guard must be held across `.await` points
- Use `tokio::sync::RwLock` for read-heavy shared state
- Hold locks for the minimum duration; no `.await` while holding `std::sync::MutexGuard`

---

## Channels

```rust
// One-shot — single value, one sender, one receiver
use tokio::sync::oneshot;
let (tx, rx) = oneshot::channel::<String>();
tokio::spawn(async move { tx.send("hello".into()).ok(); });
let msg = rx.await?;

// Multi-producer single-consumer (mpsc)
use tokio::sync::mpsc;
let (tx, mut rx) = mpsc::channel::<Job>(100); // bounded

tokio::spawn(async move {
    while let Some(job) = rx.recv().await {
        process(job).await;
    }
});

// Multiple senders via clone
for _ in 0..4 {
    let tx = tx.clone();
    tokio::spawn(async move {
        tx.send(Job::new()).await.ok();
    });
}
drop(tx); // close channel when all senders dropped

// Broadcast — multiple receivers
use tokio::sync::broadcast;
let (tx, _) = broadcast::channel::<Event>(1000);
let mut rx1 = tx.subscribe();
let mut rx2 = tx.subscribe();
```

---

## Select

`tokio::select!` races multiple async operations; the first to complete wins.

```rust
use tokio::time::{sleep, Duration};

async fn with_timeout<T>(
    future: impl Future<Output = T>,
    timeout: Duration,
) -> Option<T> {
    tokio::select! {
        result = future => Some(result),
        _ = sleep(timeout) => None,
    }
}

// Select on multiple channels
loop {
    tokio::select! {
        Some(job) = job_rx.recv() => handle_job(job).await,
        Some(signal) = signal_rx.recv() => {
            if signal == Signal::Shutdown { break; }
        }
        else => break, // all channels closed
    }
}
```

---

## Send and Sync

- `Send`: a type can be transferred across thread boundaries (all fields must be `Send`)
- `Sync`: a type can be shared via `&T` across threads (`T: Sync` if and only if `&T: Send`)
- `Rc<T>` is neither `Send` nor `Sync` — use `Arc<T>` for shared ownership across threads
- `RefCell<T>` is `Send` but not `Sync` — use `Mutex<T>` for shared mutable access

The compiler enforces `Send`/`Sync` automatically based on field types. Manually implementing them is `unsafe` and requires proving the invariants.

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `std::sync::Mutex` guard held across `.await` | Deadlock | Use `tokio::sync::Mutex` |
| Spawning unbounded tasks | Memory exhaustion under load | Use `JoinSet` with max size or `Semaphore` |
| `.unwrap()` on `Mutex::lock()` in server code | Panics if mutex is poisoned | Handle `PoisonError` or use `tokio::sync::Mutex` (no poisoning) |
| Shared mutable state via `Arc<Mutex<T>>` everywhere | Contention bottleneck | Prefer message passing (channels) for coordination |
| `block_on` inside async context | Panics in tokio runtime | Use `.await` instead |
