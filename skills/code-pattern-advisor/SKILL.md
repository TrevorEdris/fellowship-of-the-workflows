---
name: code-pattern-advisor
description: >
  Identifies the right software design pattern for a given coding task. Use this skill
  whenever the user is designing a class, module, system, or architecture and would benefit
  from a known pattern — or when they're about to misapply one. Triggers include: asking
  "what pattern should I use", "how should I structure this", "is there a better way to
  organize this code", refactoring discussions, architecture planning, code review where
  structural improvements are relevant, or any task involving object creation strategies,
  decoupling components, managing state, handling errors across boundaries, or coordinating
  complex workflows. Also trigger when the user is ALREADY using a pattern and you detect
  they may be misapplying it or overengineering — the skill covers anti-patterns and
  "when NOT to use" guidance with equal weight. This skill is language-agnostic but
  accounts for language idioms that replace patterns natively.
user-invocable: true
argument-hint: "[design problem, pattern question, or file/directory to review]"
agent: code-pattern-advisor
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git status), Bash(git branch:*), Bash(gh pr view:*), Bash(gh pr diff:*), Read, Grep, Glob, LS
tags: [architecture, review]
tier: core
---

# Code Pattern Advisor

Analyze code for design pattern correctness using the code-pattern-advisor agent.

## Context

GIT STATUS:

```
!`git status 2>/dev/null || echo "(not a git repository — no local changes to show)"`
```

FILES MODIFIED:

```
!`gh pr diff --name-only 2>/dev/null || git diff --name-only origin/HEAD... 2>/dev/null || git diff --name-only HEAD`
```

DIFF CONTENT:

```
!`gh pr diff 2>/dev/null || git diff --merge-base origin/HEAD 2>/dev/null || git diff HEAD`
```

## Objective

Use the code-pattern-advisor agent to review the code above for misapplied, unnecessary, or missing design patterns. Detect over-engineering, under-engineering, language idiom violations, and pattern misapplication. Your final reply must contain the markdown report.

## References

- `references/diagnostic_framework.md` — Diagnostic steps and pattern quick-reference
- `references/creational_patterns.md` — Factory Method, Abstract Factory, Builder, Prototype, Singleton, Object Pool
- `references/structural_patterns.md` — Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy
- `references/behavioral_patterns.md` — Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor
- `references/data_and_domain_patterns.md` — Repository, Value Object, Entity, Aggregate Root, DTO, Data Mapper, Active Record, CQRS, Unit of Work, Specification, Anti-Corruption Layer, Domain Event
- `references/functional_patterns.md` — Result/Either, Option/Maybe, Railway-Oriented Programming, Monad patterns
- `references/anti_patterns.md` — Golden Hammer, Speculative Generality, God Object, Anemic Domain Model, Singleton abuse, Premature Abstraction, Pattern Soup, Lava Flow
- `references/language_idioms.md` — Maps GoF patterns to native language features (Python, JS/TS, Rust, Go, C++, Java, C#, Kotlin, Swift)
