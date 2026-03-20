# Anti-Patterns Reference

An anti-pattern is a common solution that appears helpful but actually creates more
problems than it solves. This reference covers both general anti-patterns AND the specific
misapplication of good patterns.

This file is arguably the most important reference in the skill. The priorities are:
(1) when to apply a pattern, (2) when NOT to apply one. This file serves priority #2.

---

## Golden Hammer

**"When all you have is a hammer, everything looks like a nail."**

**What it looks like:**
- Using the same pattern everywhere regardless of context. Every service gets Repository
  + Unit of Work + CQRS, even the ones that are just reading a config file.
- Choosing a pattern because the team knows it, not because the problem requires it.
- "We always use [X pattern]" as a team rule applied without judgment.

**Why it happens:** Familiarity breeds comfort. Once a developer learns a pattern and sees
it work well, they naturally reach for it again. This is human nature, not stupidity — but
it leads to over-engineering.

**The fix:** Start by identifying the problem, not the solution. Ask "what structural
tension exists here?" before asking "which pattern should I apply?" If you can't articulate
the problem the pattern solves in this specific case, you don't need the pattern.

---

## Speculative Generality

**"We might need this flexibility someday."**

**What it looks like:**
- Interfaces with one implementation ("in case we need another one later")
- Factory classes that create only one type
- Abstract classes with one subclass
- Strategy pattern with one strategy
- Configuration systems for things that never change
- Builder pattern for objects with 3 fields

**Why it happens:** Developers are taught to plan for change. But planning for the WRONG
change is worse than not planning at all, because you've added complexity along an axis
that never varies while potentially making it harder to change along the axis that does.

**The fix:** Follow YAGNI (You Aren't Gonna Need It). Add abstraction when you have a
concrete second use case, not before. It's almost always easier to extract an interface
when you need one than to maintain a premature abstraction that turns out to be wrong.

---

## God Object / God Class

**What it looks like:**
- A single class that knows too much and does too much
- Hundreds or thousands of lines in one file
- Dependencies on everything; everything depends on it
- Methods that serve unrelated purposes living on the same class
- "Utils" or "Manager" or "Helper" classes that accumulate miscellaneous logic

**Why it happens:** Incrementalism. Each new feature is easiest to add to the existing
class that already has the context. No single addition seems unreasonable, but the
accumulation is.

**The fix:** Single Responsibility Principle. Ask "what is the one reason this class would
change?" If there are multiple independent reasons, it should be multiple classes.
Extract responsibilities into focused classes. Facade can help provide a simple interface
if the resulting decomposition feels too fragmented to clients.

---

## Anemic Domain Model

**What it looks like:**
- Entity/model classes that are just bags of getters and setters with no behavior
- All business logic lives in "service" classes that manipulate entities externally
- Entities are essentially DTOs with database mapping annotations
- The domain model doesn't protect its own invariants

**Why it happens:** Database-first thinking. Developers model entities as table rows, add
ORM annotations, and then write services to "do stuff" with the data. Also happens when
teams cargo-cult DDD structure (entities, repositories, services) without the DDD
philosophy (rich domain models, bounded contexts, ubiquitous language).

**When the Anemic Model is actually fine:**
- The domain is genuinely simple (CRUD). Not every application has complex business rules.
- The team is small, velocity matters more than architectural purity, and the domain
  doesn't justify the investment in a rich model.
- You're building a thin layer over a database for reporting or admin purposes.

**When it's a real problem:**
- Business rules are duplicated across multiple services because entities don't enforce
  their own invariants.
- The domain is complex but the model doesn't reflect that complexity — instead, the
  complexity lives in a tangled web of services.

**The fix:** Push behavior onto the entities and value objects where it belongs. An Order
should know how to add an item, validate its own state, and calculate its total. A
service should coordinate across aggregates, not implement the business logic of any
single one.

---

## Singleton Abuse

Singleton is both a pattern and, when misused, an anti-pattern. See the Singleton entry
in `creational_patterns.md` for the full treatment. The summary here:

**What it looks like when it's an anti-pattern:**
- Global mutable state accessible from anywhere
- Classes depend on Singletons but this isn't visible in their constructors or interfaces
- Tests fail intermittently because Singletons carry state between test cases
- "We need a Singleton for the database connection... and the cache... and the logger...
  and the config... and the user session..." — accumulation of global state

**The fix:** Dependency injection. Pass dependencies explicitly through constructors.
This makes dependencies visible, testable, and replaceable.

---

## Premature Abstraction

**What it looks like:**
- Creating abstractions before there's a concrete need for them
- Writing a "flexible" system that handles cases that don't exist yet
- Architecture astronautics: designing for millions of users when you have 12
- "Let's make it configurable" for everything

**Why it's harmful:** Premature abstractions are almost always wrong abstractions. Without
concrete use cases, you're guessing where the variation will be. When real requirements
arrive, they rarely align with your guesses, and now you have a wrong abstraction that's
harder to change than no abstraction at all.

**The Rule of Three:** Wait until you have three concrete use cases before extracting a
common abstraction. With one case, you don't know what varies. With two cases, you might
see a pattern but can't be sure. With three, the common structure usually becomes clear.

**The fix:** Write concrete code first. Refactor to abstractions when duplication and
variation demonstrate a real need. Keep things simple until complexity forces your hand.

---

## Pattern Soup

**What it looks like:**
- A codebase that uses 15 different patterns in a 2000-line application
- Every class participates in at least two patterns
- Reading the code requires a GoF reference book open beside you
- New developers take weeks to understand the architecture because of indirection layers
- "Follow the pattern" is the answer to every design question, even when it doesn't apply

**Why it happens:** Enthusiasm after learning patterns. Desire to demonstrate skill.
Cargo-culting from architecture books that describe enterprise-scale patterns but don't
emphasize that most apps don't need them.

**The fix:** Patterns are tools, not ornaments. Each pattern should solve a specific,
articulable problem. If you can't explain what problem a pattern solves in your code to
a junior developer in one sentence, reconsider whether it belongs.

---

## Lava Flow

**What it looks like:**
- Dead code, unused abstractions, and deprecated patterns left in the codebase because
  nobody knows if something depends on them
- "Don't touch that, it might break something" said about code nobody understands
- Layers of architectural decisions from different eras coexisting uncomfortably
- Patterns that were introduced, partially implemented, and abandoned

**Why it happens:** Fear of removing code. Lack of tests. Developer turnover. Partially
completed refactors.

**The fix:** Tests. Version control (you can always get it back). Regular cleanup passes.
The courage to delete code that isn't earning its keep.

---

## Cargo Cult Architecture

**What it looks like:**
- "Netflix uses CQRS and Event Sourcing, so we should too" (you have 100 users, not
  100 million)
- Microservices for a team of 3 developers
- Repository + Unit of Work + CQRS + Event Sourcing + Saga for a CRUD app
- Applying every DDD pattern because you read the book, without evaluating whether your
  domain is complex enough to justify it

**Why it happens:** Success stories from large companies are inspiring. Architecture talks
at conferences showcase solutions to scale problems. Developers understandably want to
build systems "the right way." But "the right way" depends entirely on context.

**The fix:** Match the solution to the problem's actual size. A three-person startup
building a CRUD app doesn't need the architectural patterns that Netflix uses to serve
a billion requests per day. Start simple. Add patterns when specific problems force you
to — not before.

---

## Leaky Abstraction (Misapplied)

**What it looks like:**
- Repository that exposes IQueryable, letting callers write arbitrary queries and
  defeating the abstraction
- Facade that requires callers to understand the subsystem anyway
- Adapter that leaks the adapted interface's concepts
- Anti-Corruption Layer that passes through foreign types unchanged

**Why it happens:** Building a proper abstraction is hard. Taking shortcuts (exposing the
underlying thing) is easy. Gradually, the "abstraction" becomes a thin wrapper that adds
a dependency but not actual isolation.

**The fix:** If the abstraction can't hide the details, either make it stronger or remove
it. A leaky abstraction is often worse than no abstraction, because it gives a false
sense of isolation while still coupling you to the implementation.

---

## Diagnostic Checklist: Should I Apply a Pattern Here?

Run through this before recommending or implementing any pattern:

1. **Can I name the specific problem this pattern solves in this code?**
   If no → don't use it.

2. **Is there a simpler way to solve this problem?**
   A function, a simple class, a language feature? Use the simplest tool that works.

3. **Does this pattern already exist in my framework/language?**
   Don't re-implement what the language or framework provides.

4. **Will a new team member understand why this pattern is here?**
   If not, the pattern is adding confusion, not clarity.

5. **Am I adding this because I need it, or because I might need it?**
   If "might" → YAGNI. Add it when you need it.

6. **Does this pattern make the code easier or harder to change?**
   If harder (because it abstracts the wrong axis), it's counterproductive.

7. **How many patterns am I applying to this codebase?**
   If more than 3-4 in a small-to-medium project, question whether pattern soup is forming.
