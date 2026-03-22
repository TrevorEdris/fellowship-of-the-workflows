# Agent Catalog

Maps each available FotW agent to its capabilities, domain, and routing guidance. The orchestrator uses this catalog to assign subtasks to the best-fit agent.

**Important:** The dynamic agent list in the `orchestrate` SKILL.md Context section is the authoritative source of available agents. This catalog provides capability details for routing decisions. Keep them in sync.

**Agent locations:**
- `agents/` — Core agents (auto-discovered in plugin mode)
- `platforms/agents/` — Platform-specific agents (explicit install required)
- `vendors/agents/` — Vendor-specific agents (explicit install required)

---

## Routing Guide

| Agent | Domain | Best For | Model | Tools |
|-------|--------|----------|-------|-------|
| `general-purpose` | Any | Fallback, broad tasks, coordination, tasks with no specialist fit | default | All |
| `pragmatic-code-review` | Code quality | PR reviews, code analysis, refactoring feedback, architecture evaluation | opus | Bash, Glob, Grep, Read, Write, WebFetch |
| `security-review` | Security | Vulnerability scanning, authentication analysis, input validation, secret detection | opus | Bash, Glob, Grep, Read, Task |
| `aws-architect` | AWS architecture | Well-Architected reviews, service selection, cost optimization, resilience, IaC review | opus | Bash, Glob, Grep, Read, WebFetch |
| `aws-iam-auditor` | AWS IAM security | IAM policy analysis, privilege escalation detection, trust policy review, CIS compliance | opus | Bash, Glob, Grep, Read |
| `azure-architect` | Azure architecture | Azure service selection, resource sizing, region strategy, redundancy, WAF alignment, cost optimization | opus | Bash, Glob, Grep, Read, Write, WebFetch |
| `design-review` | UI/UX | Visual design review, accessibility audit, responsiveness evaluation | sonnet | Bash + Playwright MCP tools |
| `frontend-builder` | UI implementation | Distinctive frontend creation, anti-AI-slop aesthetics, accessible production-grade code with self-verification | opus | Bash, Glob, Grep, Read, Write, Edit, WebFetch + Playwright MCP tools |
| `mermaid-diagram-specialist` | Documentation | Architecture diagrams, sequence diagrams, flowcharts, system topology | (check file) | Read, Write |
| `ascii-ui-mockup-generator` | UI prototyping | Text-based UI wireframes, terminal UI mockups, layout sketching | (check file) | Read, Write |
| `codebase-pattern-finder` | Code analysis | Pattern detection, consistency checking, convention auditing across large codebases | (check file) | Glob, Grep, Read |
| `code-pattern-advisor` | Architecture/review | Design pattern misapplication, over-engineering, missing structure, language idiom violations | sonnet | Bash, Glob, Grep, LS, Read |
| `ui-ux-designer` | Design | Design system specs, component design, UX flow documentation | (check file) | (check file) |
| `tdd-enforcer` | Testing | TDD enforcement, RED-GREEN-REFACTOR cycle gating, test-first compliance | sonnet | Bash, Glob, Grep, Read |
| `systematic-debugger` | Debugging | Root cause analysis, hypothesis-driven debugging, read-only investigation | opus | Bash, Glob, Grep, Read |
| `documentation-sync` | Documentation | Post-implementation doc sync, staleness audit, changelog generation | sonnet | Bash, Glob, Grep, Read, Write |
| `desloppify` | Code/content quality | AI slop detection and removal from code comments, documentation, and prose | sonnet | Bash, Glob, Grep, LS, Read, Write, Edit |
| `refactoring-specialist` | Code quality | Code smell detection, safe refactoring execution, characterization tests | sonnet | Bash, Glob, Grep, Read, Write, Edit |
| `performance-optimization` | Performance | N+1 detection, caching analysis, bundle size, algorithmic complexity | opus | Bash, Glob, Grep, LS, Read, Task |
| `e2e-test-reviewer` | Testing | E2E/integration test quality review, AAA compliance, isolation patterns | sonnet | Bash, Glob, Grep, Read |
| `accessibility-audit` | Accessibility | WCAG 2.1/2.2 POUR audit, keyboard nav, contrast, ARIA patterns | sonnet | Bash + Playwright MCP tools |
| `multi-agent-orchestrator` | Coordination | Multi-agent task decomposition, dependency-aware delegation, failure handling | opus | Bash, Glob, Grep, Read, Write, Task |
| `scope-analyzer` | Analysis | Codebase reverse engineering, PRD extraction, scope discovery (read-only) | sonnet | Read, Grep, Glob, LS |
| `otel-instrumentation` | Observability | OTel SDK setup, Collector config, Prometheus exposition, Grafana dashboards, SLOs | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `datadog-instrumentation` | Observability | Datadog agent setup, APM tracing, DogStatsD metrics, Terraform monitors/SLOs | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `cloud-run-specialist` | GCP serverless | Cloud Run deploy/config/debug, Cloud Functions 2nd gen, Pub/Sub, Eventarc triggers, Cloud Tasks | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `gcp-iam-auditor` | GCP security | IAM policy audit, SA key file detection, over-privilege analysis, WIF configuration review | opus | Bash, Glob, Grep, Read, Write |
| `system-design-reviewer` | Architecture | Architecture review, resilience pattern gaps, distributed system hazards, scalability risks, ADR/RFC evaluation | sonnet | Read, Glob, Grep |
| `grafana-irm-specialist` | Incident Management | Grafana Cloud IRM on-call schedules, escalation chains, alert routing, Terraform grafana_oncall_* resources, mcp-grafana workflows | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `incident-io-specialist` | Incident Management | incident.io Slack-native incident response, automation workflows, catalog modeling, Terraform provider v5+, MCP server workflows | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `better-stack-specialist` | Incident Management | Better Stack uptime monitors, on-call policies, status pages, Terraform BetterStackHQ/better-uptime provider, MCP server workflows | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `pagerduty-config` | Alerting/On-call | PD service design, escalation policies, on-call schedules, Events API v2, event orchestration, Terraform pagerduty provider | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `terraform-specialist` | Infrastructure-as-code | Terraform module authoring, state management, provider patterns, security audit, CI/CD pipeline setup | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `terragrunt-specialist` | Infrastructure-as-code | DRY Terragrunt root configs, dependency DAG design, run-all orchestration, multi-account patterns | sonnet | Bash, Glob, Grep, Read, Write, WebFetch |
| `aws-iac-specialist` | Infrastructure | CloudFormation, CDK, SAM authoring and review; IAM least-privilege; cdk-nag/cfn-lint security scanning; CFN→CDK migration | sonnet | Bash, Glob, Grep, Read, Write |
| `pulumi-specialist` | Infrastructure | Pulumi program authoring (TS/Python/Go/C#), CrossGuard policy packs, state backend config, Terraform/CFN migration, multi-cloud patterns | sonnet | Bash, Glob, Grep, Read, Write |
| `chaos-engineer` | Adversarial review | Failure mode analysis, race conditions, security gaps, edge cases, pessimistic code review (read-only) | opus | Bash, Glob, Grep, LS, Read, WebFetch |
| `team-lead` | Agent Teams coordination | Creates and manages Agent Teams, spawns teammates, coordinates via shared task list and messaging. Claude Code only. | opus | Bash, Glob, Grep, Read, Write, Task, SendMessage |

---

## Routing Rules

Apply these rules in order when selecting an agent for a subtask:

1. **Match domain first.** If a subtask clearly belongs to a single domain (security, code quality, diagram generation), assign the specialist for that domain.

2. **Prefer specialists over general-purpose.** Specialist agents have domain-specific frameworks and produce higher-quality output within their domain. Reserve `general-purpose` for tasks that genuinely span domains or have no specialist fit.

3. **Split mixed-domain subtasks.** If a subtask description covers two distinct domains (e.g., "review the code and update the diagram"), split it into two subtasks — one per domain — rather than assigning it to `general-purpose`.

4. **Use `general-purpose` as universal fallback.** If a specialist agent fails after retry, `general-purpose` can attempt any domain. Its output may be less precise but is better than a halt.

5. **Consider model tier for critical subtasks.** `opus` agents (`pragmatic-code-review`, `security-review`) have stronger reasoning for complex analysis. For simple, mechanical subtasks (e.g., "rename this variable across 3 files"), a default-model agent is sufficient and faster.

6. **Check the dynamic list before routing.** If the `ls agents/` output in the skill context shows agents not listed here, they may be available — check their frontmatter for capability hints before assigning.

---

## Agent Capability Details

### `general-purpose`

The default catch-all. Use when:
- No specialist covers the required domain
- The task is multi-domain and splitting would create excessive overhead
- A specialist has failed and you need a fallback

Does not have domain-specific frameworks but has access to all tools and can handle most tasks with sufficient context in the handoff.

### `pragmatic-code-review`

Applies the Pragmatic Quality framework:
- Architecture and design integrity
- Functional correctness and edge cases
- Security (surface-level; for deep security analysis use `security-review`)
- Maintainability, naming, complexity
- Testing strategy
- Performance and scalability
- Dependencies and documentation

Uses the FotW triage matrix: [CRITICAL] / [HIGH] / [MEDIUM] / [LOW].

Best invoked with specific files or a diff to review, not an entire repository.

### `security-review`

Applies the Anthropic security methodology with >80% confidence threshold. Focuses on:
- Input validation vulnerabilities (SQLi, command injection, path traversal)
- Authentication and authorization flaws
- Cryptographic weaknesses and secret exposure
- Injection and code execution vectors
- Data exposure risks

Explicitly excludes DoS, rate limiting, and theoretical issues. Every finding includes confidence score and concrete exploit scenario.

### `design-review`

Requires Playwright MCP tools to be available. Evaluates:
- Visual hierarchy and layout
- Color contrast and accessibility (WCAG compliance)
- Responsiveness across viewport sizes
- Interaction patterns and usability

Best invoked with a running URL or screenshot, not static code alone.

### `mermaid-diagram-specialist`

Generates and refines Mermaid diagram syntax for:
- Architecture diagrams (C4, system context, container)
- Sequence diagrams (API flows, event handling)
- Flowcharts (decision trees, process flows)
- Entity-relationship diagrams

Output is Mermaid markdown that can be rendered in GitHub, Notion, and most documentation tools.

### `ascii-ui-mockup-generator`

Creates text-based UI wireframes using ASCII/Unicode box-drawing characters. Useful for:
- Early-stage layout exploration without visual design tools
- Terminal UI and CLI interface mockups
- Documentation-embedded wireframes that render in any text editor

### `codebase-pattern-finder`

Analyzes code at scale to identify:
- Repeated patterns and potential abstractions
- Convention violations and inconsistencies
- Dead code and unused exports
- Cross-cutting concerns that may benefit from refactoring

Best for large codebases where manual pattern detection is impractical.

### `code-pattern-advisor`

Detects misapplied, unnecessary, or missing design patterns in code. Applies a four-category detection framework: over-engineering (pattern soup, speculative generality, factories creating one type, builders for 3-field objects), under-engineering (God objects, anemic domain models, missing value objects), language idiom violations (GoF ceremony where language provides native equivalent — Strategy→lambda, Visitor→pattern matching, Builder→named params), and misapplication (wrong pattern for the problem — Adapter between owned interfaces, leaky Repository, Mediator with business logic). Read-only — diagnoses but does not fix. Use over `pragmatic-code-review` when the primary concern is structural pattern correctness rather than general code quality; use over `codebase-pattern-finder` when the goal is evaluating pattern appropriateness rather than finding repeated code structures; use alongside `refactoring-specialist` when pattern findings should be acted on immediately.

Best invoked with specific files or a diff to review, plus context about the language and architectural style in use; providing the team size and codebase scale helps calibrate recommendations (patterns justified for a 50-person team may be over-engineering for a solo developer).

### `ui-ux-designer`

Produces design specifications and UX documentation:
- Component design specs
- Design system guidelines
- User flow diagrams
- Interaction specifications for handoff to developers

### `tdd-enforcer`

Enforces strict test-driven development discipline by gating each phase of the RED-GREEN-REFACTOR cycle with explicit entry and exit conditions. Detects the project's test runner automatically (package.json, pyproject.toml, go.mod, Cargo.toml, Makefile, Taskfile) and blocks production code from being written until a failing test exists. Use over `pragmatic-code-review` when the goal is to drive new implementation, not evaluate existing code; use over `refactoring-specialist` when adding new behavior rather than restructuring existing behavior.

Best invoked with a clear description of the behavior to implement and access to the repository so it can detect the test runner and run the suite at each phase gate.

### `systematic-debugger`

Investigates bugs using a mandatory four-phase methodology: root cause investigation, pattern analysis, hypothesis testing, and a structured findings report. Read-only — it cannot write or edit files, which prevents premature fixes before root cause is confirmed. Use over `pragmatic-code-review` when a bug needs deep investigation rather than code quality feedback; after this agent confirms root cause, delegate the actual fix to a code-writing agent.

Best invoked with a specific symptom (error message, stack trace, reproduction steps) and recent git diff context; the more concrete the symptom, the more targeted the investigation.

### `documentation-sync`

Analyzes git diffs and code changes to generate or update README sections, changelogs, and API documentation, using `<!-- AUTO-GENERATED:START -->` markers to protect hand-written content. Classifies docs by staleness (FRESH / SLIGHTLY_STALE / STALE / VERY_STALE) and follows Keep a Changelog format with conventional commit classification rules. Use over `mermaid-diagram-specialist` for prose/reference documentation; use after implementation is complete rather than during, since it generates from actual code state.

Best invoked after a batch of changes are committed, with the git diff range or list of changed files provided so it can map source changes to their documentation owners.

### `desloppify`

Identifies and removes AI-generated noise from code and text across three domains:
- **Code comments:** narrator, step, obvious, over-documented, placeholder, apologetic, redundant type docs (9 patterns)
- **Code patterns:** defensive impossible-case handling, unnecessary try-catch, redundant type assertions, premature abstraction, speculative generality (8 patterns)
- **Prose:** filler phrases, AI vocabulary, promotional adjectives, structural tells, surface-level treatment

Operates in four modes: `code`, `docs`, `prose`, and `review` (report-only). Uses four-severity triage (CRITICAL/HIGH/MEDIUM/LOW) and presents proposed changes for user approval before applying. Use over `pragmatic-code-review` when the concern is AI-generated noise specifically; use over `writing-clearly-and-concisely` when detecting and removing existing slop rather than learning writing principles; use alongside `refactoring-specialist` when AI noise coexists with structural smells.

Best invoked after AI-assisted code generation or editing, with specific files or a git diff range to scope the scan; auto-detect mode uses `git status` to identify recently changed files.

### `refactoring-specialist`

Applies a catalog of named code smells (Bloaters, Object-Orientation Abusers, Change Preventers, Dispensables, Couplers) and maps each to its canonical refactoring technique, executing transformations in small atomic steps with a full test suite run after each. Establishes a green baseline first and writes characterization tests if none exist — it will not proceed with a red suite. Use over `pragmatic-code-review` when you need structural changes executed, not just identified; use over `tdd-enforcer` when improving existing code without adding behavior.

Best invoked with a target file or directory and a description of the structural concern (e.g., "this class has too many responsibilities"), or simply pointed at the scope to let it run smell detection and propose a prioritized plan.

### `performance-optimization`

Applies a six-category static analysis framework — database/query performance, algorithmic complexity, memory/resource management, caching strategy, bundle/payload size, and I/O/network — prioritized by user-facing impact. Distinguishes confirmed anti-patterns in hot paths from theoretical concerns and quantifies impact in measurable terms (extra queries per request, Big-O class, latency ms). Use over `pragmatic-code-review` when performance is the primary concern; for frontend-only bundle analysis or backend-only query tuning, still use this agent but provide the relevant context to narrow its focus.

Best invoked with context about the expected load (request rate, data volume, which paths are user-facing) and the specific component under analysis rather than an entire monorepo.

### `e2e-test-reviewer`

Reviews E2E and integration test files against a hierarchical quality framework covering test design, AAA structure, isolation guarantees, selector resilience (data-testid/ARIA over CSS/XPath), wait strategies, mock boundaries, artifact configuration, and maintainability. Does not review application logic — its scope is exclusively how tests are written. Use over `pragmatic-code-review` for test file reviews where structural correctness and flakiness risk are the primary concerns; use after `tdd-enforcer` has driven the implementation to validate the resulting tests meet E2E quality standards.

Best invoked with a path to the test directory or specific test files, and ideally the Playwright config file so it can validate artifact and retry configuration.

### `accessibility-audit`

Conducts a comprehensive WCAG 2.1/2.2 audit using the POUR framework (Perceivable, Operable, Understandable, Robust), executing live browser tests via Playwright MCP for contrast calculations, keyboard navigation mapping, and accessibility tree inspection. Applies a 0.7 confidence threshold — findings must be verified against a running browser, not inferred from static code. Use over `design-review` when WCAG compliance and access barriers are the explicit concern; use alongside `design-review` on the same feature only if both visual design and standards compliance need separate, thorough passes.

Best invoked with a running URL and specific routes or components to test; without Playwright MCP available, it cannot execute the required browser-based verification steps.

### `multi-agent-orchestrator`

Decomposes large multi-domain tasks into atomic subtasks via a five-phase protocol (Intake, Decomposition, Delegation, Failure Handling, Aggregation), routes each subtask to the best-fit agent from the FotW catalog, manages dependency ordering with maximum parallelism, and handles failures via retry/fallback/skip/halt escalation. Presents the decomposition plan to the user and waits for explicit approval before delegating — it does not perform specialist work itself. Use when a task spans two or more agent domains (code + tests + docs + security) or when parallel execution across independent workstreams would materially reduce wall time.

Best invoked with a complete task description including scope boundaries, hard constraints, and preferences for agent or model tier; ambiguous scope triggers clarifying questions before decomposition begins.

### `scope-analyzer`

Performs read-only codebase reverse engineering by systematically working through ten discovery sources in priority order (routing, tests, UI components, modules, interfaces, dependency graph, directory structure, data flow, documentation, infrastructure), stopping at saturation (three consecutive sources with no new findings). Produces a structured scope report with confidence-scored functional units (High = 3+ sources, Medium = 2, Low = 1). Use before planning a large feature or migration to establish a reliable functional map; use over `codebase-pattern-finder` when the goal is understanding what the system does rather than how the code is organized.

Best invoked with a target path and optional focus area (e.g., "authentication only") to constrain discovery scope; it is strictly read-only and will not run shell commands or modify files.

### `otel-instrumentation`

Instruments backend services with production-grade OpenTelemetry observability: OTel SDK setup for Go/Node.js/Python/Rust, OTel Collector pipeline configuration (receivers, processors, exporters), Prometheus metrics exposition, structured logging with trace correlation, Grafana RED method dashboard templates, and SLO definitions with multi-window burn-rate AlertManager rules. Enforces naming conventions (snake_case, `_total` suffix for counters, base units), cardinality discipline, and the RED method (Rate, Errors, Duration) as the baseline signal set. Use over `datadog-instrumentation` when the observability stack is OTel-native, Prometheus, or Grafana; use alongside `datadog-instrumentation` only if the Collector is configured to export to both backends.

Best invoked with the target service's language, framework, and existing observability stack identified; providing existing `go.mod`, `package.json`, or `pyproject.toml` lets it select the correct SDK packages without guessing.

### `datadog-instrumentation`

Instruments backend services using the Datadog platform: unified service tagging (DD_ENV/DD_SERVICE/DD_VERSION, mandatory first step), Datadog agent and DaemonSet configuration, APM tracing via ddtrace SDK or Single Step Instrumentation for containers, DogStatsD custom metrics with cardinality budgeting (350 unique tag combinations per metric), log correlation using decimal trace IDs, and Terraform-managed monitors and SLOs with burn-rate alerting. Enforces symptom-based alerting (error rate and latency) and rejects cause-based pages (CPU, memory). Use over `otel-instrumentation` when the target observability platform is Datadog; the two agents have compatible health-check and SLO patterns but different SDK dependencies, log field names (decimal vs hex trace IDs), and infrastructure-as-code approaches (Terraform vs PromQL/AlertManager).

Best invoked with the target service's language and deployment environment (Docker Compose, Kubernetes) specified; if Terraform state or existing `datadog.yaml` is available, providing it avoids duplicating monitor definitions.

### `system-design-reviewer`

Reviews architecture decisions, system designs, RFCs, and ADRs against distributed systems best practices across six dimensions: resilience (timeouts, retry, circuit breaker, idempotency, DLQ), distributed system correctness (dual-write elimination, saga compensation, eventual consistency), scalability (stateless services, caching, connection pools, N+1 patterns), data ownership (service boundaries, multi-tenancy isolation, schema compatibility), security (auth at service boundary, secret management), and operational readiness (SLOs, health checks, tracing, runbooks). Produces a scored, tiered findings report using [CRITICAL] / [HIGH] / [MEDIUM] / [LOW] severity levels. Use over `pragmatic-code-review` when the concern is architectural correctness and distributed system hazards rather than code quality; use before or alongside `pragmatic-code-review` for comprehensive review coverage.

Best invoked with a design document, RFC, ADR, or structured system description that includes: components, data flows, external dependencies, expected load, and consistency requirements. Without a description of external dependencies and consistency model, the agent will ask clarifying questions before producing findings.

### `pagerduty-config`

Configures the PagerDuty notification and escalation layer: PD service design (service boundaries, one service per logical concern domain), escalation policy construction (3-level max, standard L1/L2/L3 timeouts), on-call schedule design with rotation layers and coverage gap validation, Events API v2 payload design including `dedup_key` naming (`{service}:{alert_rule}:{env}` pattern) and trigger/acknowledge/resolve lifecycle, event orchestration rules (global and service-level DAG), severity mapping from AlertManager/Datadog/Grafana to PD severity, noise tiering (page/notify/log), and Terraform `hashicorp/pagerduty` provider v3.x resources. The key contract with the observability agents: this agent produces an `integration_key` output (from `pagerduty_service_integration`) that `datadog-instrumentation` and `otel-instrumentation` consume as the `routing_key` for their monitoring tools. Use after observability agents have defined SLOs and alerting rules — PD config is downstream. Use over the observability agents when the task is about who gets paged and when, not what triggers the page.

Best invoked after the monitoring stack is defined (`datadog-instrumentation` or `otel-instrumentation` work is complete); provide the list of services, team names, and whether Terraform is already managing any PD resources so it can generate import commands for existing ones.

### `terraform-specialist`

Implements and reviews Terraform configurations using a five-category quality framework: state management (remote backend, locking, per-environment isolation), security (secrets in secrets manager, OIDC for CI, least-privilege IAM, Checkov scanning), module structure (standard layout, root vs child boundaries, semver pinning), resource quality (`for_each` vs `count`, `lifecycle` rules, `moved` blocks), and testability (`terraform validate`, `tflint`, native `terraform test`). Applies the FotW triage matrix with severity labels from blocking (hardcoded credentials, local state) to polish (naming, comment clarity). Generates complete, runnable HCL — no stubs. Use over `pragmatic-code-review` for Terraform-specific pattern enforcement; use over `security-review` when the concern is IaC security misconfigurations rather than application-level vulnerabilities.

Best invoked with the specific `.tf` files or module directory to review or the resource requirements to implement; providing existing `.terraform.lock.hcl` and `versions.tf` lets it match pinned provider versions without guessing.

### `terragrunt-specialist`

Designs and reviews Terragrunt configurations for multi-account, multi-region infrastructure: root `terragrunt.hcl` with `remote_state` and `generate` blocks, DRY provider/backend elimination, path-based state keys, `dependency` and `dependencies` block design, mock outputs for CI plan-on-PR, DAG visualization and cycle detection, `run --all` orchestration with scope flags and parallelism tuning, destroy gates, and migration guidance from plain Terraform. Proactively recommends plain Terraform when Terragrunt's complexity is unjustified (single account, <10 modules, <3 environments). Use after `terraform-specialist` has established module quality — Terragrunt orchestrates Terraform modules, it does not replace them.

Best invoked with the folder hierarchy structure and a description of the account/region/environment model; providing the existing root `terragrunt.hcl` (if any) and a list of units with their dependencies produces the most accurate DAG design.

### `azure-architect`

Provides Azure architecture guidance grounded in the Azure Well-Architected Framework (WAF) five pillars: Reliability, Security, Cost Optimization, Operational Excellence, and Performance Efficiency. Applies structured service selection tables (compute, data, messaging), region and Availability Zone redundancy analysis, RBAC and Managed Identity security baseline by default, and cost estimation with Reserved Instance and lifecycle policy recommendations. Produces structured architecture decision records with service selection tables, redundancy strategy, security baseline, cost estimate, and trade-off analysis. Reads actual IaC and code before making recommendations — does not rely on conversation context alone. Use over `pragmatic-code-review` when the concern is Azure service selection and architecture design rather than code quality; use over `security-review` when the concern is Azure IAM posture and Managed Identity design rather than application-level vulnerabilities.

Best invoked with a concrete requirement set (availability SLA, throughput, data residency, budget) and the current IaC or architecture diagram; providing existing Bicep/Terraform files lets it evaluate the current state before recommending changes.

### `grafana-irm-specialist`

Configures Grafana Cloud IRM (the merged product of Grafana OnCall + Grafana Incident) for on-call scheduling, escalation chain design, alert routing from Prometheus Alertmanager or Grafana Alerting, and Slack ChatOps integration. Generates Terraform using the `grafana/grafana` provider (v3+) with `grafana_oncall_integration`, `grafana_oncall_escalation_chain`, `grafana_oncall_escalation`, `grafana_oncall_schedule`, and `grafana_oncall_on_call_shift` resources. Guides teams through MCP-driven incident operations using the official `mcp-grafana` server (dashboards, alert groups, Loki log queries, incident creation and timeline). Handles migration from Grafana OnCall OSS (archived March 2026) to Grafana Cloud IRM. Use over `incident-io-specialist` when the team is already on Grafana Cloud with Prometheus/OTel — zero additional vendor; use over `better-stack-specialist` when deep metric visualization and alerting on Prometheus rules is the primary concern.

Best invoked with the Grafana Cloud stack URL and API key available; providing existing Alertmanager config lets it generate the correct integration webhook routing without guessing receiver names.

### `incident-io-specialist`

Configures incident.io for Slack-native incident management: severity levels, incident types, incident roles, automation workflows (Slack channel auto-creation, lead auto-assignment, postmortem creation), catalog modeling (Service/Team/Feature types), on-call schedules, and escalation policies. Generates Terraform using the official `incident-io/incident` provider (v5+). Guides teams through the official incident.io MCP server (Claude-native, remote, no local install) for AI-driven incident operations: declaring incidents, querying on-call, catalog lookups, and postmortem preparation. Handles OpsGenie migration (EOL April 2027) including schedule export, policy recreation, and webhook URL updates. Use over `grafana-irm-specialist` when the team is Slack-native and wants structured incident workflows rather than pure alert routing; use over `better-stack-specialist` when the primary need is incident response tooling rather than uptime monitoring.

Best invoked with the incident.io API key and Slack workspace already connected (Slack connection must be done via UI before Terraform); providing the team structure and existing OpsGenie export (if migrating) allows direct schedule recreation.

### `better-stack-specialist`

Configures Better Stack as a consolidated replacement for uptime monitoring, on-call scheduling, and status pages. Generates Terraform using the `BetterStackHQ/better-uptime` provider with `betterstack_monitor`, `betterstack_monitor_group`, `betterstack_on_call_calendar`, `betterstack_escalation_policy`, `betterstack_status_page`, `betterstack_status_page_section`, and `betterstack_status_page_resource` resources. Configures multi-region HTTP, keyword, SSL, TCP, and cron heartbeat monitors with correct confirmation and recovery periods. Guides status page setup including custom domains, subscriber management, and Statuspage.io migration. Integrates with the Better Stack MCP server for AI-driven incident operations and log queries. Use over `grafana-irm-specialist` and `incident-io-specialist` when cost consolidation is the primary driver and the team does not need deep APM or Slack-native incident workflows; strongest fit for startups and mid-market teams (< 200 engineers) currently paying for multiple single-purpose tools.

Best invoked with the list of services to monitor, their health check URLs, and the team's existing status page URL if migrating; providing current vendor costs (Pingdom + PagerDuty + Statuspage.io) enables a concrete consolidation recommendation.

### `aws-iac-specialist`

Authors and reviews AWS infrastructure-as-code using CloudFormation, CDK, and SAM. Applies the AWS Well-Architected Framework security pillar by default: least-privilege IAM (no `Action: "*"` or `Resource: "*"` without justification), `DeletionPolicy: Retain` on stateful resources, `NoEcho: true` on all sensitive parameters. For CDK: enforces L2 over L1 construct selection (L2 sets encryption and public access defaults automatically), runs `cdk-nag` security scanning as a standard step, and writes assertions tests using `aws-cdk-lib/assertions`. Performs CloudFormation→CDK migrations mapping each `AWS::*` resource type to its CDK L2 equivalent. Applies the FotW triage matrix ([CRITICAL] / [HIGH] / [LOW]). Use over `terraform-specialist` for AWS-native tooling (CFN/CDK/SAM); use `terraform-specialist` for multi-cloud or when HCL is already the team standard; use `pulumi-specialist` for Pulumi-based AWS programs.

Best invoked with the IaC tool already identified (or let it auto-detect from `cdk.json`, `template.yaml`, `samconfig.toml`); providing existing templates or CDK stacks enables a direct review against actual code rather than hypothetical patterns.

### `pulumi-specialist`

Authors Pulumi programs in TypeScript, Python, Go, and C#; writes CrossGuard policy packs; configures state backends; interprets `pulumi preview` output; and migrates from Terraform HCL or CloudFormation using `pulumi convert`. Enforces Output/Input typing discipline (never calls `.get()` in production code; uses `.apply()`, `pulumi.all()`, and `pulumi.interpolate` for Output transformations), the `<project>/<env>` stack naming convention, and the no-local-backend rule for shared environments. Applies the FotW triage matrix for reviews. Use over `aws-iac-specialist` when the project uses Pulumi regardless of cloud provider; use over `terraform-specialist` when Pulumi's multi-language or CrossGuard capabilities are the deciding factor; use alongside `terraform-specialist` only during incremental migration where both tools coexist.

Best invoked with `Pulumi.yaml` content and active stack identified; providing the target language (TypeScript default), cloud provider(s), and state backend lets it generate complete, runnable programs without guessing configuration.

### `aws-architect`

Reviews AWS workloads against the AWS Well-Architected Framework's five pillars: Operational Excellence, Security, Reliability, Performance Efficiency, and Cost Optimization. Evaluates IaC (CDK, SAM, CloudFormation, Terraform), service selection, networking topology, and cross-cutting concerns. Flags common anti-patterns (wildcard IAM, single-AZ databases, Lambda in VPC without endpoints, on-demand DynamoDB for predictable traffic). Produces structured findings with pillar attribution and remediation priority. Use over `pragmatic-code-review` when the concern is cloud architecture quality rather than application code quality; use over `aws-iam-auditor` when the scope is broader than IAM alone.

Best invoked with IaC files and a description of expected load, compliance requirements, and cost targets; without load context, performance and cost findings will be qualitative rather than quantitative.

### `aws-iam-auditor`

Analyzes IAM policies, role trust relationships, and compliance posture through read-only static analysis of provided policy documents, IaC code, or `aws iam get-account-authorization-details` output. Identifies wildcard permissions, privilege escalation paths (17 known patterns including `iam:CreatePolicyVersion`, `iam:PassRole` + `iam:AttachRolePolicy`, Lambda code update escalation), over-permissive trust policies, and hardcoded credential patterns. Evaluates against CIS AWS Foundations v1.5 controls by default; supports SOC 2, PCI DSS, and HIPAA scoping. Produces findings rated Critical/High/Medium/Low with specific evidence and remediation JSON. This agent is strictly read-only — it will not run any write commands or access live AWS APIs. Use over `security-review` when the concern is IAM preventive controls rather than application-level vulnerabilities; use alongside `aws-architect` for a complete security posture review.

Best invoked with specific IAM JSON documents or IaC files; `aws iam get-account-authorization-details --output json > audit.json` provides the broadest input for a full account audit.

### `cloud-run-specialist`

Operates GCP serverless compute and async messaging: Cloud Run service deployments (image, traffic splits, min-instances, secrets, VPC egress), Cloud Run Jobs for batch workloads, Cloud Functions 2nd gen (HTTP and event-triggered), Pub/Sub topic/subscription design (push vs pull, dead-letter topics, flow control), Eventarc trigger configuration (GCS, Audit Logs, Pub/Sub), Cloud Tasks queues, and Cloud Scheduler cron jobs. Enforces security defaults: dedicated service accounts, `--no-allow-unauthenticated` for internal services, secrets injected from Secret Manager, and dead-letter topics on all production Pub/Sub subscriptions. Uses a safe traffic-migration protocol (deploy with `--no-traffic`, verify, then promote). Does not cover IAM role bindings beyond minimum service wiring (defer to `gcp-iam-auditor`), observability instrumentation (defer to `otel-instrumentation` or `datadog-instrumentation`), or CI/CD pipeline configuration (defer to `/cicd-pipeline`).

Best invoked with the Cloud Run service name, region, and container image URL; providing the current service config via `gcloud run services describe` lets it detect drift from secure defaults without guessing.

### `chaos-engineer`

Adversarial code reviewer that assumes the worst about every change. Applies a six-category attack surface methodology: Failure Modes (unhandled errors, partial failures, timeout cascading), Concurrency (race conditions, deadlocks, stale reads), Input Boundaries (overflow, malformed data, encoding edge cases), Error Path Coverage (uncaught exceptions, swallowed errors, misleading messages), Dependency Failures (upstream outages, version drift, transitive vulnerabilities), and State Corruption (inconsistent state, missing rollback, orphaned resources). Read-only — critiques but never fixes. Use over `security-review` when the concern is operational resilience and failure scenarios rather than OWASP-style vulnerability patterns; use alongside `pragmatic-code-review` for a pessimistic counterbalance to standard review.

Best invoked with a specific diff or set of files to review; providing context about the production environment (traffic volume, SLAs, deployment topology) helps it prioritize findings by blast radius.

### `team-lead`

Agent Teams coordinator (Claude Code only). Creates teams via Agent Teams primitives, spawns teammates from predefined rosters, manages a shared task list, and synthesizes results. Unlike `multi-agent-orchestrator` (which uses subagents), teammates communicate directly with each other via peer-to-peer messaging. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to be enabled.

Best invoked via the `/team` skill with a predefined roster (review, implementation, investigation). Not a general-purpose coordinator — use `multi-agent-orchestrator` for subagent-based orchestration.

### `frontend-builder`

Creates distinctive, production-grade frontend interfaces that avoid generic AI aesthetics. Follows a design thinking phase (purpose, tone, constraints, differentiation) before writing code, then implements with bold typography, color, motion, and layout choices. Bakes in WCAG 2.1 AA accessibility from the start (semantic HTML, keyboard navigation, contrast, ARIA). Self-verifies output using Playwright (screenshots at 3 viewports, keyboard navigation check, console error check).

Best used as part of the `ui-creation-team` roster where a `ui-ux-designer` provides aesthetic direction and an `accessibility-audit` agent validates the output. Can also be invoked standalone for UI implementation tasks where the design direction is already established. Use over `ascii-ui-mockup-generator` when real code (not wireframes) is needed; use over `general-purpose` when the task is frontend creation requiring distinctive aesthetics.

### `gcp-iam-auditor`

Audits GCP IAM policy for over-privilege, public access bindings (`allUsers`/`allAuthenticatedUsers`), user-managed service account key files, default compute SA abuse, and missing Workload Identity Federation for CI/CD workloads. Applies the FotW triage matrix ([CRITICAL] / [HIGH] / [MEDIUM] / [LOW]) and produces a prioritized findings report with exact remediation `gcloud` commands. Strictly read-only during audit phase — presents specific remediation commands and waits for confirmation before executing any changes. Use over `security-review` when the concern is GCP infrastructure IAM posture rather than application-level vulnerabilities; use over `aws-iam-auditor` for GCP workloads; use after `cloud-run-specialist` deployment to validate the resulting IAM configuration.

Best invoked with `gcloud config list` output to establish the active project; running with broad IAM read permissions (`roles/iam.securityReviewer` or `roles/viewer`) enables the most complete audit. If permissions are restricted, the agent will note the gaps.

---

---

## Community Agents

These agents live in `community/agents/` and are **not** auto-discovered in plugin mode. Install them explicitly:

```bash
./bin/fotw install agents/terraform-specialist ~/project --for claude-code
```

| Agent | Domain | Best For |
|-------|--------|----------|
| `terraform-specialist` | Infrastructure-as-code | Terraform module authoring, state management, security audit |
| `terragrunt-specialist` | Infrastructure-as-code | DRY Terragrunt configs, dependency DAGs, multi-account patterns |
| `aws-iac-specialist` | AWS IaC | CloudFormation, CDK, SAM authoring; CFN→CDK migration |
| `aws-architect` | AWS architecture | Well-Architected reviews, service selection, IaC review |
| `aws-iam-auditor` | AWS IAM security | IAM policy analysis, privilege escalation, CIS compliance |
| `azure-architect` | Azure architecture | Azure service selection, WAF alignment, cost optimization |
| `pulumi-specialist` | Infrastructure | Pulumi programs (TS/Python/Go/C#), CrossGuard, CFN/TF migration |
| `cloud-run-specialist` | GCP serverless | Cloud Run, Cloud Functions, Pub/Sub, Eventarc, Cloud Tasks |
| `gcp-iam-auditor` | GCP security | GCP IAM audit, over-privilege, Workload Identity Federation |
| `datadog-instrumentation` | Observability | Datadog APM, DogStatsD metrics, Terraform monitors/SLOs |
| `otel-instrumentation` | Observability | OTel SDK, Collector config, Prometheus, Grafana dashboards |
| `pagerduty-config` | Alerting/On-call | PD services, escalation policies, on-call schedules, Terraform |
| `grafana-irm-specialist` | Incident Management | Grafana Cloud IRM on-call, alert routing, Terraform resources |
| `incident-io-specialist` | Incident Management | incident.io Slack-native incidents, automation, Terraform v5+ |
| `better-stack-specialist` | Incident Management | Better Stack monitors, on-call, status pages, Terraform |

---

## Adding New Agents

When a new agent is added to `agents/` (core) or `community/agents/` (community):

1. Add a row to the Routing Guide table (or Community Agents table for community agents)
2. Add a capability details section
3. Verify the `ls agents/` output in the skill context reflects the new agent (for core agents)

The orchestrator dynamically lists agents at invocation time, so new agents are immediately available for routing — the catalog is supplementary routing guidance, not a gate.
