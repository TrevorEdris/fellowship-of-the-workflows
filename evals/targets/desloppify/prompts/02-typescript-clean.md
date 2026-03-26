Review this TypeScript file for AI slop:

```typescript
import { Redis } from "ioredis";

interface CacheEntry<T> {
  value: T;
  expiresAt: number;
}

/**
 * Two-tier cache: in-memory LRU backed by Redis.
 * Memory tier avoids Redis round-trip for hot keys.
 * TTL is enforced at both tiers independently.
 */
export class TieredCache<T> {
  private memory = new Map<string, CacheEntry<T>>();

  constructor(
    private redis: Redis,
    private prefix: string,
    private ttlSeconds: number,
    // Keep memory tier small to avoid GC pressure on large datasets
    private maxMemoryEntries = 1000
  ) {}

  async get(key: string): Promise<T | null> {
    const memEntry = this.memory.get(key);
    if (memEntry && memEntry.expiresAt > Date.now()) {
      return memEntry.value;
    }

    const raw = await this.redis.get(`${this.prefix}:${key}`);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as T;
    this.setMemory(key, parsed);
    return parsed;
  }

  async set(key: string, value: T): Promise<void> {
    this.setMemory(key, value);
    // EX sets TTL in seconds; Redis handles expiry server-side
    await this.redis.set(
      `${this.prefix}:${key}`,
      JSON.stringify(value),
      "EX",
      this.ttlSeconds
    );
  }

  private setMemory(key: string, value: T): void {
    if (this.memory.size >= this.maxMemoryEntries) {
      // Evict oldest entry (Map preserves insertion order)
      const oldest = this.memory.keys().next().value;
      if (oldest) this.memory.delete(oldest);
    }
    this.memory.set(key, {
      value,
      expiresAt: Date.now() + this.ttlSeconds * 1000,
    });
  }
}
```
