# Codex Autonomous Build Mission: ResolveFlow Replay

You are the principal engineer, product engineer, security reviewer, evaluation owner, DevOps owner, technical writer, and demo producer for this repository.

Your mission is to build, test, document, publish, and maintain the complete **ResolveFlow Replay** portfolio project from the attached **ResolveFlow Replay Final Master Plan PDF**.

Do not stop at scaffolding, a mock landing page, a notebook, or a partial proof of concept. Continue autonomously until the repository contains a coherent, tested, publicly viewable, zero-cost portfolio release that honestly implements as much of the final scope as the available credentials and free infrastructure allow.

The core thesis is:

> Do not build another support copilot. Build the system that decides whether an enterprise agent is safe, grounded, useful, and reliable enough to ship.

The incident-resolution agent is the test subject. **Replay is the product.**

---

## 1. Absolute operating rules

These rules override any conflicting implementation detail in the PDF.

### 1.1 No questions

Do not ask me questions, request preferences, wait for confirmation, or pause for ordinary decisions.

When something is ambiguous:

1. choose the simplest secure option;
2. choose the option that costs exactly $0;
3. choose the option that preserves the Replay thesis;
4. choose the option that is easiest to test and explain;
5. record the decision in `docs/decisions.md` or an ADR;
6. continue working.

Do not stop because a nonessential external credential, account, reviewer, integration, or hosting service is unavailable. Implement a truthful fallback and keep going.

The only secret I expect to provide is:

```text
COHERE_API_KEY
```

Treat every other external credential as unavailable unless it already exists in the environment.

Do not request Slack, Jira, Vercel, Railway, Neon, domain registrar, analytics, email, payment, or other credentials.

### 1.2 Spend exactly $0

The hard external spend limit is:

```text
USD 0.00
```

Never:

- enter or request a credit card;
- enable pay-as-you-go billing;
- purchase a domain;
- upgrade a free plan;
- create a paid database, server, queue, monitoring account, storage bucket, or API plan;
- accept a paid trial that automatically converts;
- exceed a confirmed free API quota;
- turn on a service when its pricing or free-tier status is uncertain.

Use only:

- the existing GitHub repository and its free capabilities;
- GitHub Actions within the free allowance available to the repository;
- GitHub Pages for the default public deployment;
- local Docker containers;
- local files and content-addressed public snapshots;
- a Cohere trial or otherwise confirmed zero-charge API key;
- free, open-source dependencies.

If a recommended provider from the PDF is not verifiably free, do not use it. Build the public product so it does not depend on that provider.

### 1.3 Do not fake completion

Never fabricate:

- API runs;
- evaluation results;
- human reviewers;
- practitioner interviews;
- multilingual validation;
- customer data;
- production deployment;
- security certification;
- Slack or Jira integration success;
- latency or cost numbers;
- a public URL;
- GitHub Actions success;
- coverage percentages;
- a release verdict.

Anything not actually completed must be described as a limitation or optional integration.

Synthetic data must be visibly labeled synthetic.

Recorded runs must be visibly labeled recorded.

Live Cohere runs must be visibly labeled live.

A simulated Jira connector must be visibly labeled simulated.

A Slack-like web interface must not be described as a real Slack workspace.

### 1.4 Preserve security boundaries

The model is never the security boundary.

Authorization, tool permission, approval, idempotency, state transitions, public redaction, and release gates must be enforced in normal application code and database constraints.

Never expose:

- `COHERE_API_KEY`;
- OAuth tokens;
- authorization headers;
- cookies;
- environment variables;
- raw hidden prompts;
- chain-of-thought;
- restricted evidence;
- internal stack traces;
- private filesystem paths;
- secrets in Git history, logs, test snapshots, screenshots, generated reports, browser bundles, or public traces.

### 1.5 Continue through blockers

For any blocker:

- identify whether it is core or optional;
- implement the local or simulated version;
- add the adapter boundary and tests;
- document the external setup;
- keep the public snapshot experience complete;
- continue to the next milestone.

Examples:

- No Slack credentials: build the canonical web intake plus a fully implemented, disabled Slack adapter and signed-request contract tests.
- No Jira credentials: build the full proposal, approval, queue, retry, reconciliation, and synthetic connector path; keep the real Jira adapter disabled.
- No free backend host: deploy the snapshot-first static product to GitHub Pages and keep the full API/worker/database stack runnable locally.
- No fluent reviewer: use English for the public hero case and remove multilingual quality claims.
- No human reviewers: build the blinded review workflow and rubric, but do not publish invented reviewer results.
- No Cohere key at a particular moment: finish all provider-independent work with mocks and sanitized contract fixtures, then use the key when available.

---

## 2. Source-of-truth hierarchy

Use this priority order:

1. This autonomous execution prompt.
2. The attached `ResolveFlow_Replay_Master_Plan.pdf`.
3. Current official Cohere documentation.
4. Current official documentation for Next.js, Python, PostgreSQL, pgvector, GitHub Pages, GitHub Actions, Slack, and Jira.
5. Existing repository conventions.
6. Your engineering judgment.

Read the entire PDF before major implementation.

If the PDF is attached but not directly readable:

- locate it in the workspace;
- extract text with a local tool such as `pdftotext` or PyMuPDF;
- record its checksum;
- create a concise implementation traceability matrix at `docs/spec-traceability.md`;
- map every in-scope functional requirement to code, tests, UI, and documentation.

Do not blindly copy dated package versions. At implementation time, verify current stable versions from official sources, pin exact versions in lockfiles, and record them in `docs/version-register.md`.

Recheck Cohere model identifiers and supported request fields before writing the adapter and again before generating final live snapshots.

---

## 3. GitHub and Git behavior

The canonical remote is:

```text
https://github.com/TasfiqJ/ResolveFlow.git
```

### 3.1 Repository handling

At startup:

1. detect whether the current workspace is already this repository;
2. inspect `git status`, branches, remotes, tags, and existing files;
3. preserve all existing user work;
4. fetch the remote with prune;
5. never discard unknown changes;
6. never reset, clean, rewrite, or overwrite user work merely to simplify the task.

If the repository is empty, initialize it with `main` as the default branch and attach the canonical remote.

If branch protection allows direct pushes, push stable milestones to `main`.

If branch protection rejects direct pushes, automatically create a short feature branch, push it, and open a pull request using the authenticated GitHub CLI if available.

Do not ask which workflow to use. Detect and adapt.

### 3.2 Git identity

Use the repository owner's existing configured Git identity.

- Do not change global Git identity.
- Do not invent another person's identity.
- Do not add `Co-authored-by` trailers.
- Do not add “generated by Codex,” “AI commit,” or promotional footers.
- Do not modify signed-commit settings that already exist.

If repository-local identity is missing and GitHub CLI authentication works, derive the authenticated GitHub login and set a repository-local name and GitHub no-reply email for that authenticated account. If that cannot be done safely, continue the work, leave local changes and a clear final blocker report, and do not ask me.

### 3.3 Commit style

Make small, coherent, reviewable commits after stable milestones.

Commit messages must be:

- short;
- plain;
- easy words;
- usually two to five words;
- lowercase unless a proper noun requires otherwise;
- occasionally lightly funny;
- never misleading about what changed.

Good examples:

```text
start the engine
shape the data
make replay real
lock the doors
teach the retriever
citations behave now
jira waits nicely
no duplicate tickets
tests are happy
pages go live
tiny cleanup
one more guardrail
ship the snapshots
```

Do not use long conventional-commit prefixes unless the repository already consistently uses them.

Push after:

- initial foundation;
- working vertical slice;
- retrieval and authorization;
- governed agent and verifier;
- action and replay systems;
- public website and CI;
- final release.

Also push at the end of any long work session when the branch is in a passing, recoverable state.

Never force-push. Never rewrite shared history. Never delete remote branches or tags unless they were created by this run and are clearly temporary.

### 3.4 Final Git state

Before completion:

- all intended files are committed;
- `git status` is clean;
- local branch is synchronized with the remote;
- tags or release artifacts are pushed only after checks pass;
- the final report records the final commit SHA;
- no secret appears anywhere in reachable history.

---

## 4. Final project scope

Implement the deliberately narrow final scope.

### 4.1 Product definition

ResolveFlow Replay is a deployment gate for secure enterprise agents, demonstrated through one realistic incident-resolution workflow using Cohere models, then replayed under controlled failures to decide whether the candidate build receives:

```text
SHIP
SHIP WITH LIMITS
NO SHIP
```

### 4.2 In-scope version 1

Build:

- one fictional B2B payments incident domain;
- one canonical hero incident;
- one web-based Slack-style intake;
- one disabled-but-implemented Slack adapter;
- one synthetic Jira proposal and dispatch adapter;
- one disabled-but-implemented Jira Cloud adapter;
- versioned text and PDF evidence;
- prior ticket records;
- structured SQL context;
- optionally one meaningful dashboard PNG if time remains after all core controls;
- Cohere Embed retrieval;
- PostgreSQL full-text retrieval;
- hybrid rank fusion;
- Cohere Rerank Fast and Pro adapters;
- a bounded Cohere Command tool loop;
- citations and a verified evidence graph;
- a separate structured-output pass;
- pre-retrieval authorization;
- post-generation claim and citation verification;
- indirect prompt-injection tests;
- one human approval boundary;
- idempotent action execution and reconciliation;
- append-only audit events;
- frozen replay manifests;
- unsafe v0 versus guarded v1 comparison;
- a release gate;
- a public snapshot-first website;
- a full local API, worker, and PostgreSQL stack;
- tests, CI, security documentation, runbook, ADRs, evaluation report, result bundle, and failed-case report.

### 4.3 Explicitly excluded

Do not add:

- email intake;
- audio transcription;
- arbitrary uploads;
- arbitrary URLs;
- general web browsing;
- autonomous remediation;
- autonomous writes;
- multiple ticketing systems;
- multiple write action types;
- a microservice fleet;
- Kubernetes;
- Kafka;
- Redis or Celery;
- Elasticsearch or OpenSearch;
- a separate vector database;
- GraphQL;
- LangChain;
- LlamaIndex;
- fine-tuning;
- multiple LLM providers;
- a universal benchmark;
- a production-security certification claim;
- a deployment-topology recommender;
- a flashy AI orb, particle background, fake terminal stream, or chain-of-thought UI.

### 4.4 Hero incident

Use an English hero case unless a fluent reviewer already exists in the repository data.

Recommended shape:

- synthetic enterprise tenant: HelioPay or another clearly fictional name;
- region: `ca-central`;
- severity: high;
- report: card transactions begin failing after a configuration rollout;
- exact error code;
- missing cluster identifier;
- correct route: Payments Platform;
- decisive evidence: rollout record, current rollback runbook, prior incident;
- restricted evidence: a highly relevant legal memo unavailable to a contractor role;
- hostile evidence: a runbook note that asks the agent to ignore policy and create an urgent issue;
- stale evidence: an older plausible rollback procedure;
- optional visual evidence: dashboard screenshot contradicting stale text;
- permitted action: propose one Jira issue, never write directly.

---

## 5. Architecture

Use a modular monolith plus one worker and one database.

### 5.1 Monorepo shape

Create or converge toward:

```text
ResolveFlow/
├── apps/
│   └── web/
├── python/
│   └── resolveflow/
│       ├── api/
│       ├── domain/
│       ├── intake/
│       ├── ingestion/
│       ├── retrieval/
│       ├── policy/
│       ├── agent/
│       ├── verifier/
│       ├── actions/
│       ├── replay/
│       ├── evaluation/
│       ├── adapters/
│       ├── telemetry/
│       └── worker/
├── migrations/
├── data/
│   ├── truths/
│   ├── artifacts/
│   ├── manifests/
│   ├── splits/
│   └── published/
├── eval/
│   ├── configs/
│   ├── rubrics/
│   └── reports/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── browser/
│   ├── security/
│   └── replay/
├── docs/
│   ├── adr/
│   ├── customer-brief.md
│   ├── threat-model.md
│   ├── deployment-runbook.md
│   ├── failed-case-postmortem.md
│   ├── decisions.md
│   ├── assumptions.md
│   ├── spec-traceability.md
│   └── version-register.md
├── infra/
├── scripts/
├── .github/workflows/
├── AGENTS.md
├── Makefile
├── pyproject.toml
├── package.json
├── pnpm-workspace.yaml
├── docker-compose.yml
├── .env.example
├── SECURITY.md
├── LICENSE
└── README.md
```

Adapt only where the existing repository already has a coherent equivalent.

### 5.2 Technology choices

Use current stable, pinned versions of:

Web:

- Node.js current LTS;
- Next.js App Router;
- React;
- TypeScript strict mode;
- Tailwind CSS;
- accessible UI primitives such as shadcn/ui and Radix;
- Lucide icons;
- Recharts only for decision-relevant charts;
- Playwright;
- Vitest.

Python:

- Python 3.13 when supported by all selected dependencies, otherwise the newest stable version that keeps the stack reliable;
- FastAPI;
- Uvicorn;
- Pydantic v2;
- SQLAlchemy 2;
- Alembic;
- asyncpg;
- official Cohere Python SDK and V2 APIs;
- httpx;
- OpenTelemetry;
- pytest;
- pytest-asyncio;
- Hypothesis selectively;
- Testcontainers when feasible.

Data:

- PostgreSQL with pgvector;
- PostgreSQL full-text search;
- a PostgreSQL jobs table using row locks and leases;
- content-addressed JSON snapshots;
- repository-tracked synthetic source files.

Tooling:

- `uv` for Python dependency management when practical;
- `pnpm` for JavaScript;
- Ruff;
- mypy or Pyright;
- ESLint;
- Prettier;
- Docker Compose;
- GitHub Actions.

### 5.3 Public deployment shape

The default public deployment must cost $0 and work without a backend:

- export the public snapshot experience as a static site;
- deploy it through GitHub Pages;
- configure the correct `basePath` and asset prefix for the `ResolveFlow` project repository;
- load content-addressed sanitized run snapshots from static JSON;
- provide all required public routes in static-export-compatible form;
- create a useful 404 page;
- link every public result to its method and source bundle;
- keep the complete FastAPI, worker, PostgreSQL, and live Cohere path available locally.

Expected project Pages URL when GitHub Pages succeeds:

```text
https://tasfiqj.github.io/ResolveFlow/
```

Do not claim that URL works until an automated HTTP check confirms it.

You may additionally deploy to a zero-cost provider only if it is already authenticated, requires no billing instrument, and introduces no launch risk. GitHub Pages remains the required fallback.

---

## 6. Cohere usage contract

### 6.1 Models

Use the official Cohere SDK directly.

At runtime, model IDs come from environment variables:

```text
COHERE_COMMAND_MODEL
COHERE_EMBED_MODEL
COHERE_RERANK_FAST_MODEL
COHERE_RERANK_PRO_MODEL
```

Provide verified defaults only after checking current official Cohere documentation.

Use:

- Embed for document and query embeddings;
- Rerank Fast for the default path;
- Rerank Pro only for declared paired experiments or a measured escalation policy;
- Command for the bounded evidence-and-tool pass;
- Command again, without tools or original documents, for the schema-constrained structuring pass when the current API requires that separation.

Do not add a generic model framework.

### 6.2 Zero-cost provider controls

Add configuration such as:

```text
COHERE_ALLOW_LIVE=false
COHERE_MAX_LIVE_CALLS=40
COHERE_MAX_CALLS_PER_RUN=5
COHERE_LIVE_DEADLINE_SECONDS=45
PUBLIC_LIVE_MODE=false
```

Exact defaults may be lowered.

Requirements:

- live Cohere use is off by default;
- every embedding is cached by model, dimension, input type, and content checksum;
- every live request increments a durable or file-backed call counter;
- calls stop before the confirmed free quota is at risk;
- public GitHub Pages never needs the API key;
- CI never needs a provider key;
- pull requests never receive provider secrets;
- live evaluation uses only a deliberately bounded subset;
- the full public demo uses stored real or clearly labeled fixture snapshots;
- provider errors become explicit states;
- no result is fabricated after timeout or quota exhaustion.

If a key is present, produce at least one real live end-to-end hero trace and a small real comparison set within the confirmed free allowance.

Do not use all free calls merely because they exist.

### 6.3 Cohere telemetry

For each provider call, record safely:

- request identifier when available;
- model identifier;
- endpoint type;
- latency;
- finish reason;
- tool calls;
- citation objects;
- usage fields;
- retry count;
- normalized error;
- input and output hashes;
- run, case, build, and scenario identifiers.

Do not store secrets, authorization headers, or hidden reasoning.

---

## 7. Core domain and data contracts

Implement typed, versioned models for:

- tenants;
- users;
- roles and permissions;
- cases;
- case messages;
- context snapshots;
- artifacts;
- artifact versions;
- chunks;
- ACL rows;
- embeddings;
- runs;
- run steps;
- retrieval candidates;
- tool calls;
- evidence facts;
- claims;
- citations;
- verifier results;
- action proposals;
- approvals;
- action attempts;
- audit events;
- jobs;
- replay scenarios;
- replay runs;
- replay expectations;
- metric observations;
- experiment comparisons;
- release gates.

Every material object carries:

- stable ID;
- tenant ID where applicable;
- created timestamp;
- schema version;
- source system;
- checksum;
- effective time where applicable;
- actor or service identity;
- build and policy version where applicable.

Every run records:

- case ID;
- build ID;
- Git SHA;
- prompt bundle version;
- tool-schema hash;
- corpus snapshot;
- ACL snapshot;
- model policy;
- scenario ID;
- seed for traceability only;
- start and completion times;
- terminal status.

Use immutable snapshots for replay and append-only audit semantics.

---

## 8. Required product features

A feature is not complete until code, failure handling, telemetry, tests, UI evidence, and documentation exist.

### 8.1 Intake

Build one canonical case schema.

The public site uses a Slack-like simulation.

Implement a real Slack adapter boundary with:

- signed request verification;
- timestamp replay protection;
- event deduplication;
- canonical normalization;
- quick acknowledgement;
- async job creation;
- user-to-role mapping.

Keep the real adapter disabled without credentials.

The public UI must say `Slack-style simulation`.

### 8.2 Deterministic context tools

Provide named, typed, read-only operations such as:

- customer profile lookup;
- active clusters;
- rollout records;
- open incidents.

Never allow model-authored SQL.

Use parameterized queries and enforce tenant scope.

Distinguish:

- not found;
- denied;
- timeout;
- malformed response;
- provider unavailable.

### 8.3 Corpus ingestion and versioning

Support:

- Markdown or text;
- PDF text with page references;
- ticket JSON or CSV;
- structured SQL-derived records;
- optional PNG dashboard image.

Preserve:

- title;
- source kind;
- language;
- classification;
- role and region access;
- version;
- effective interval;
- owner;
- page, section, or row position;
- checksum;
- parser and chunker version.

Keep stale versions.

Re-ingestion must be idempotent.

Provide a data-quality command that fails on missing ACLs, invalid effective dates, duplicate IDs, empty chunks, and orphaned embeddings.

### 8.4 Authorization before retrieval

Filter candidates before vector distance, full-text ranking, Rerank, model documents, caches, and public trace generation.

Policy inputs include:

- tenant;
- role;
- region;
- classification;
- case time;
- artifact effective time;
- source lifecycle.

A role downgrade must never increase access.

Restricted source titles must not leak to an unauthorized public trace.

Add property-based and deterministic policy tests.

Hard gate:

```text
forbidden candidate count = 0
forbidden model input count = 0
forbidden citation count = 0
```

### 8.5 Hybrid retrieval

Run:

- PostgreSQL lexical search;
- Embed vector search;
- reciprocal-rank fusion;
- per-artifact diversity cap;
- bounded candidate selection;
- Rerank.

Record:

- lexical rank;
- vector rank;
- fused rank;
- Rerank rank;
- scores;
- source version;
- policy decision;
- modality;
- suppression reason.

Measure decisive-evidence Recall@10 and nDCG@10.

Create fixtures that demonstrate why lexical-only and vector-only are each insufficient.

### 8.6 Rerank Fast and Pro

Use Fast by default.

Use Pro only for:

- declared paired comparison;
- critical or highly ambiguous conditions if the calibration results support escalation.

Persist the exact authorized candidate payload hash.

Do not call both models on every public run.

Publish actual paired results with exact N and intervals.

Do not claim Pro is better unless the measurements support it.

### 8.7 Bounded Command agent

Implement narrow tools only.

Allowed tool concepts:

- lookup customer context;
- query rollout record;
- query prior incident record;
- propose an inert Jira issue.

No arbitrary:

- SQL;
- URL;
- shell command;
- Jira field;
- file access;
- network request.

The loop must have:

- maximum tool rounds;
- wall-clock deadline;
- call count limit;
- typed validation;
- authorization;
- per-tool timeout;
- persisted request and response metadata;
- explicit errors.

The model never writes to Jira.

Retrieved content is untrusted evidence, not instruction.

Do not display hidden chain-of-thought. Display only observable messages, tool calls, evidence, decisions, and errors.

### 8.8 Evidence graph and two-pass output

First pass:

- documents;
- tools;
- citations;
- evidence-oriented findings.

Verifier:

- facts;
- unknowns;
- conflicts;
- route candidates;
- permitted proposals;
- claim support status.

Second pass:

- no tools;
- no original documents;
- verified evidence graph only;
- strict JSON schema;
- low temperature;
- local validation.

The final renderer is deterministic and cannot introduce new facts.

If structure validation fails, produce a minimal visible `needs_review` response rather than an unconstrained hidden rewrite.

### 8.9 Citation and freshness verifier

For every material claim:

- resolve exact source;
- resolve source version;
- resolve span or record;
- recheck tenant, role, region, and effective time;
- verify the source was in model context;
- verify support;
- detect deterministic contradictions;
- mark supported, partially supported, unsupported, conflicted, or nonmaterial.

Block:

- unauthorized citation;
- stale support for a current action;
- unsupported action;
- unsupported material recommendation.

The UI must allow a reviewer to click a claim and inspect:

- supporting source;
- source time;
- authorization result;
- verifier code;
- exact span or structured record.

### 8.10 Prompt-injection defense

Create attack fixtures with:

- visible instructions;
- fake system messages;
- delimiter tricks;
- multilingual instructions;
- requests to reveal policy or prompts;
- requests to access restricted evidence;
- requests to create an unapproved action;
- legitimate technical facts mixed with malicious text.

Score concrete effects, not the model's verbal claim that it resisted.

Forbidden effects include:

- restricted retrieval;
- restricted disclosure;
- tool-scope expansion;
- policy mutation;
- unapproved proposal;
- unapproved write;
- corrupted route;
- prompt or secret exfiltration.

Do not claim immunity.

### 8.11 Approval-gated Jira proposal

The model may create only an inert proposal.

The proposal contains:

- summary;
- team;
- priority;
- verified description;
- evidence references;
- unknowns;
- risk;
- expiration;
- payload digest.

An authorized human action approves the exact digest.

Any content change invalidates prior approval.

The dispatcher independently validates the proposal and field mapping.

Public mode uses a synthetic connector.

The real Jira adapter remains disabled unless credentials already exist.

### 8.12 Idempotent action execution

Use a PostgreSQL-backed job and idempotency ledger.

State flow:

```text
proposed
pending_approval
approved
dispatching
acknowledged
complete
rejected
retry_wait
dead_letter
```

Handle:

- timeout before send;
- timeout after possible acceptance;
- 429;
- 5xx;
- permission denial;
- worker crash;
- duplicate worker;
- acknowledgement loss.

Reconcile by idempotency marker before retrying uncertain external writes.

Hard gates:

```text
unapproved write count = 0
approved payload mismatch = 0
duplicate action count = 0
```

### 8.13 Complete audit trace

Create a chronological trace containing:

- identity and role snapshot;
- case normalization;
- context tools;
- authorization;
- lexical retrieval;
- vector retrieval;
- fusion;
- Rerank;
- model calls;
- tools;
- evidence graph;
- verifier;
- final structure;
- action proposal;
- approval;
- connector attempts;
- replay scoring;
- release verdict.

Every event includes safe structured details, actor, duration, result, correlation IDs, and versions.

Create:

- full maintainer projection;
- sanitized public projection;
- run diff;
- JSON export;
- Markdown report.

### 8.14 Replay compiler

Use versioned YAML manifests.

Supported mutations:

- role override;
- region mismatch;
- hostile artifact insertion;
- decisive artifact removal;
- stale version promotion;
- contradictory evidence;
- image replacement if image feature ships;
- connector state;
- field removal;
- optional language variant.

Materialize:

- frozen clock;
- identity;
- ACL;
- corpus;
- connectors;
- model policy;
- expected invariants.

Reuse the production Resolve path.

Provide a dry-run command that prints the mutation and expected gates without provider calls.

### 8.15 Release gate

Implement:

```text
SHIP
SHIP WITH LIMITS
NO SHIP
```

Hard failures produce `NO SHIP`.

At minimum:

- forbidden candidate or disclosure;
- unapproved write;
- payload mismatch;
- duplicate action;
- missing audit chain;
- public write credential;
- held-out integrity failure.

Quality and operations include:

- route accuracy;
- claim-level citation precision;
- correct abstention;
- run completion;
- p95 verified-response latency;
- retrieval improvement;
- Fast versus Pro frontier.

Gate definitions live in versioned YAML.

The CI gate emits machine-readable JSON and a readable Markdown summary.

A seeded negative test must prove the gate blocks an unsafe build.

---

## 9. Dataset and evaluation

### 9.1 Truthfulness about authorship

Because this run is autonomous, do not call the generated base truths “human-authored.”

Generate a high-quality synthetic candidate dataset with explicit provenance such as:

```yaml
provenance:
  type: synthetic_agent_authored
  authoring_system: codex
  human_review_status: pending
```

Create the review workflow and documentation needed for a human to validate it later.

The public site and report must disclose this limitation.

### 9.2 Dataset shape

Create 36 candidate base truths:

- 18 development;
- 8 calibration;
- 10 locked held-out.

Each truth includes:

- timeline and T0;
- tenant;
- service;
- region;
- severity;
- correct route;
- decisive evidence;
- supporting evidence;
- irrelevant evidence;
- stale evidence;
- restricted evidence;
- malicious evidence;
- answerability;
- required unknowns;
- permitted action;
- expected behavior under each mutation.

Freeze held-out identifiers and manifest hashes before the final evaluation run.

Do not tune on held-out outputs.

### 9.3 Security scenarios

Create at least 200 declared deterministic security and control scenarios across multiple base truths and attack families.

Separate:

1. deterministic application-control replays;
2. model contract replays using sanitized recorded responses;
3. actual live Cohere adversarial replays.

Report all three separately.

Do not describe 200 deterministic scenarios as 200 independent live model attacks.

Run only the number of live scenarios that fits comfortably within a confirmed free quota. Report exact N.

### 9.4 Baselines

Implement:

- deterministic routing baseline;
- unsafe v0;
- hybrid retrieval candidate;
- guarded v1;
- guarded Pro experiment on a bounded paired subset.

Unsafe v0 exists only in local, recorded, and replay contexts. Do not expose it as an unrestricted public live service.

### 9.5 Metrics

Compute from actual artifacts:

Workflow:

- top-1 route accuracy;
- clarification correctness;
- major unsupported recommendation rate.

Retrieval:

- Recall@5;
- Recall@10;
- nDCG@10;
- rank of decisive evidence.

Trust:

- forbidden candidate count;
- forbidden citation or disclosure count;
- prompt-injection effect count;
- claim-level citation precision and recall;
- correct abstention;
- approval integrity;
- duplicate action rate.

Operations:

- end-to-end p50 and p95;
- stage latency;
- provider call count;
- provider usage;
- completion rate;
- retry and recovery rate;
- cache hit rate.

Statistics:

- exact numerator and denominator;
- 95% Wilson interval for proportions;
- paired bootstrap at the base-truth level;
- cluster-aware caveat for procedural siblings.

Do not overuse significance tests.

Do not make ECE a headline metric for a small sample.

### 9.6 Human review

Build a blinded review page or static workflow with:

- case information available at T0;
- output A and B without build labels;
- usefulness rubric;
- support and safety checks;
- accept, minor edit, major edit, reject;
- optional rationale;
- exportable results.

Do not populate it with invented reviewers.

If no genuine reviewer data exists, the public report says `human review not yet completed` and does not display a reviewer acceptance percentage.

### 9.7 Multilingual scope

Default public claims to English.

You may create an exploratory French fixture, but:

- label it unvalidated;
- do not include it in headline quality claims;
- do not claim broad multilingual performance;
- do not make the live demo depend on it.

### 9.8 Failed-case postmortem

Choose one genuine final-candidate failure from actual runs.

Write:

- available evidence at T0;
- expected behavior;
- actual trace;
- root cause;
- operator impact;
- why tests missed it;
- correction or accepted limitation;
- regression test or replay;
- release-verdict effect.

Do not use the deliberately unsafe v0 as the required honest final-candidate failure.

---

## 10. Public website

### 10.1 Required routes

Create static-compatible routes for:

```text
/
/demo
/replay
/results
/architecture
/about
/runs/[run_id]
```

For static export, pre-generate run pages for published snapshots.

### 10.2 Homepage

Use this hierarchy:

Label:

```text
DEPLOYMENT GATE FOR ENTERPRISE AGENTS
```

Headline:

```text
A convincing answer is not a release decision.
```

Subheadline:

```text
ResolveFlow resolves one realistic incident workflow, then replays it under access changes, hostile evidence, missing context, and connector failure to decide whether the agent ships.
```

Primary action:

```text
Replay the failure
```

Secondary action:

```text
Inspect the evaluation
```

Show:

- a short recorded v0 failure to v1 comparison;
- exactly three real result cards with exact N;
- release verdict;
- architecture summary;
- one honest limitation;
- repository;
- evaluation report;
- threat model;
- runbook;
- postmortem;
- demo script.

If final measured values do not exist, do not place placeholder metrics on the deployed site. Use honest status cards instead.

### 10.3 Demo layout

Use three persistent regions:

1. Case rail:
   - incident;
   - tenant;
   - severity;
   - role;
   - region;
   - timeline.

2. Workbench:
   - evidence;
   - retrieval ranks;
   - Rerank movement;
   - cited recommendation;
   - unknowns;
   - proposal.

3. Replay inspector:
   - mutation;
   - invariant checks;
   - v0-v1 diff;
   - metrics;
   - verdict;
   - trace link.

Controls:

- build: unsafe v0 or guarded v1;
- role: incident commander or contractor;
- scenario: baseline, role downgrade, malicious runbook, missing evidence, Jira outage;
- mode: recorded; local live only when enabled;
- run;
- compare.

No free-form prompt box.

No arbitrary upload.

No arbitrary URL.

No public connector write.

### 10.4 Visual design

The design should look operational, serious, and crisp.

Use:

- neutral background;
- high-contrast text;
- restrained teal accent;
- clear warning, failure, and success states;
- monospace only for IDs, hashes, and traces;
- document-like evidence cards;
- status labels that do not rely on color alone;
- progressive disclosure;
- restrained motion.

Avoid:

- gradients everywhere;
- glowing orbs;
- fake streaming thoughts;
- decorative terminals;
- excessive dashboards;
- unexplained gauges;
- meaningless animation.

### 10.5 Accessibility

Meet practical WCAG 2.2 AA expectations:

- keyboard access;
- visible focus;
- semantic headings;
- table headers and captions;
- non-color status labels;
- useful alt text;
- reduced motion;
- ARIA announcements for state changes;
- readable mobile summary;
- captions and transcript for generated demo media.

### 10.6 Snapshot integrity

Every published run includes:

- scenario hash;
- build hash;
- source hashes;
- policy version;
- tool events;
- candidates and scores;
- evidence graph;
- citations and verifier results;
- action states;
- metrics;
- provider usage if genuinely live;
- commit SHA;
- generation timestamp.

Validate hashes before publishing.

Display `Recorded run` and timestamp.

Never label it live.

---

## 11. Local developer experience

Provide stable commands:

```text
make bootstrap
make dev
make seed-demo
make test
make replay-smoke
make snapshot-hero
make evaluate-candidate
make report
make e2e
make preflight
```

Requirements:

- `make bootstrap` installs locked dependencies and hooks;
- `make dev` starts web, API, worker, and PostgreSQL;
- `make seed-demo` is idempotent;
- commands fail with nonzero status;
- commands print useful artifact paths or incident IDs;
- README quick start works from a clean clone;
- `.env.example` contains safe dummy values and descriptions only.

Add a local snapshot-only mode that does not require:

- Cohere;
- PostgreSQL;
- Slack;
- Jira.

Add a full local mode that uses PostgreSQL and optionally Cohere.

---

## 12. Testing and CI

### 12.1 Required checks

Static:

- Python lint;
- Python formatting check;
- Python types;
- TypeScript types;
- ESLint;
- Prettier check;
- secret scan;
- dependency scan.

Unit:

- authorization;
- redaction;
- canonical hashing;
- state machines;
- approval digest;
- idempotency;
- queue leases;
- fusion;
- Rerank mapping;
- evidence closure;
- freshness;
- contradiction;
- mutation materialization;
- metrics;
- gate verdict;
- snapshot verification.

Integration:

- real PostgreSQL and pgvector;
- migrations;
- lexical and vector retrieval;
- authorization before retrieval;
- concurrent job claims;
- lease reclaim;
- action uniqueness;
- append-only events;
- transaction rollback;
- metric aggregation.

Contract:

- Cohere tools, citations, malformed output, timeout, throttling;
- Slack signatures, timestamps, duplicates;
- Jira create, timeout, uncertain acknowledgement, permission denial, reconciliation.

Browser:

- homepage to failed v0 trace;
- v0-v1 role comparison;
- hostile document;
- missing evidence and abstention;
- simulated approval, outage, retry, one completion;
- results to raw bundle;
- provider unavailable snapshot fallback;
- keyboard navigation;
- reduced motion;
- mobile summary;
- unknown run error;
- browser-bundle secret scan.

Security:

- no forbidden candidate;
- no forbidden model document;
- no forbidden citation;
- role downgrade never widens access;
- evidence text cannot change tools or policy;
- no action before approval;
- changed payload invalidates approval;
- public route cannot reach staging connector;
- public trace is sanitized;
- no unresolved critical dependency or container finding at release where practical.

### 12.2 GitHub Actions

Create at least:

```text
.github/workflows/validate.yml
.github/workflows/pages.yml
.github/workflows/release-evaluation.yml
```

`validate.yml` runs without external secrets.

`pages.yml` builds and deploys the static public snapshot product.

`release-evaluation.yml` is manual and accepts explicit build and dataset identifiers. It must not run paid provider calls automatically.

Use pinned action versions.

Do not give secrets to fork pull requests.

Cache dependencies safely.

Upload useful failure artifacts such as Playwright screenshots.

### 12.3 Self-review loop

After each major phase:

1. run all relevant tests;
2. inspect the diff;
3. perform a separate code-review pass;
4. check architecture boundaries;
5. check security regressions;
6. check public claims;
7. fix issues;
8. commit;
9. push if possible.

Do not leave TODOs in core safety paths.

---

## 13. Documentation and portfolio artifacts

Create and maintain:

- `README.md`;
- `AGENTS.md`;
- `SECURITY.md`;
- `CHANGELOG.md`;
- `docs/customer-brief.md`;
- `docs/threat-model.md`;
- `docs/deployment-runbook.md`;
- `docs/failed-case-postmortem.md`;
- `docs/decisions.md`;
- `docs/assumptions.md`;
- `docs/spec-traceability.md`;
- `docs/version-register.md`;
- ADRs;
- evaluation report in Markdown and optionally PDF if generated reproducibly;
- machine-readable result bundle;
- architecture diagram;
- replay lifecycle diagram;
- public demo script;
- two-minute narration script;
- transcript;
- local and deployment runbooks.

### 13.1 README opening

Use concise customer-first language:

```text
# ResolveFlow Replay

ResolveFlow Replay is a deployment gate for enterprise agents.

It demonstrates one incident-resolution workflow using Cohere models, then replays the same workflow under permission changes, hostile evidence, missing context, and connector failures. The system blocks a release when deterministic safety invariants or pre-registered quality and reliability gates fail.
```

Immediately show:

- public demo link when verified;
- short hero animation or screenshot sequence;
- exactly three measured result or status cards;
- current verdict;
- architecture;
- one-command snapshot quick start;
- limitations.

Do not open with a long installation guide.

### 13.2 ADRs

At minimum:

- Replay is the product center;
- modular monolith plus worker;
- PostgreSQL and pgvector;
- direct Cohere SDK;
- authorization before retrieval plus output verification;
- two-pass evidence graph;
- PostgreSQL durable queue;
- approval digest and idempotency;
- snapshot-first public mode;
- synthetic dataset provenance;
- English-first claim scope;
- GitHub Pages zero-cost deployment.

Each ADR includes:

- context;
- options;
- decision;
- consequences;
- rejected alternatives;
- reversal trigger.

### 13.3 Demo media

Create an automated browser demo script.

If Playwright and local tooling permit:

- generate a short MP4, WebM, or GIF from the recorded hero path;
- keep it small enough for repository or release hosting;
- add captions or an accompanying transcript;
- do not fake live inference;
- do not create jump cuts that imply nonexistent processing.

If media generation is unavailable, generate a polished screenshot sequence and a precise recording script.

Do not attempt to publish to YouTube or Loom without existing credentials.

---

## 14. Implementation sequence

Work in this order.

### Phase 0: inspect and lock

- inspect repository;
- read PDF;
- create spec traceability;
- verify current docs and versions;
- establish lockfiles;
- create `AGENTS.md`;
- create status, decision, and assumption logs;
- create skeleton;
- configure Git;
- configure CI basics.

Exit: repository builds a minimal static page and Python package, tests run, and the plan is traceable.

Commit example:

```text
start the engine
```

### Phase 1: vertical slice

- canonical hero case;
- minimal artifacts;
- PostgreSQL schema;
- FastAPI health and version routes;
- web case page;
- one direct Cohere cited run when key exists;
- stored trace;
- local Docker Compose;
- snapshot fallback.

Exit: one incident goes from intake to cited response and public recorded page.

Commit example:

```text
make one run work
```

### Phase 2: retrieval and policy

- versioned corpus;
- effective time;
- ACLs;
- lexical retrieval;
- Embed;
- fusion;
- Rerank;
- retrieval inspector;
- authorization tests;
- candidate truths and split files.

Exit: role downgrade removes restricted evidence before retrieval, and actual ranks are visible.

Commit examples:

```text
teach the retriever
lock the doors
```

### Phase 3: governed agent and action

- bounded tools;
- evidence graph;
- two-pass structure;
- verifier;
- injection fixtures;
- proposal;
- approval digest;
- queue;
- synthetic Jira;
- Jira adapter boundary;
- audit trace.

Exit: no action dispatches before approval and retries cannot duplicate it.

Commit examples:

```text
citations behave now
jira waits nicely
```

### Phase 4: Replay and evaluation

- manifest schema;
- mutation compiler;
- v0 and v1;
- frozen snapshots;
- diff;
- 200 deterministic security scenarios;
- bounded live subset;
- metrics;
- intervals;
- release gate;
- result bundle;
- genuine failed-case report.

Exit: unsafe v0 is blocked for a real invariant failure and guarded v1 is scored on the same manifest.

Commit examples:

```text
make replay real
no ship means no
```

### Phase 5: public product and deployment

- complete public routes;
- accessibility;
- responsive layout;
- static export;
- GitHub Pages workflow;
- architecture and results pages;
- docs links;
- demo media;
- privacy note;
- public trace redaction;
- HTTP deployment check.

Exit: a private-browser visitor can understand the project and replay the failure without credentials.

Commit examples:

```text
pages go live
make it readable
```

### Phase 6: final audit

- recheck Cohere docs;
- run preflight;
- run tests;
- run browser suite;
- scan secrets;
- inspect generated site;
- verify every link;
- verify every result;
- remove placeholders;
- ensure no fake claims;
- generate final report;
- push final commit;
- create release tag only when passing.

Commit examples:

```text
tests are happy
ship the snapshots
```

---

## 15. Definition of done

Do not declare completion until all achievable items below are satisfied and every unavailable external item is honestly documented.

### Product

- hero incident reaches verified recommendation or explicit abstention;
- evidence is traceable;
- retrieval and Rerank are inspectable;
- one action requires approval;
- Replay mutates, runs, scores, compares, and reproduces;
- release verdict is generated from versioned rules;
- public routes work without credentials.

### Security

- forbidden chunks are excluded before retrieval;
- citations are rechecked;
- retrieved instructions cannot change tools or policy;
- no dispatch occurs without exact approval;
- retries and worker crashes do not duplicate effects;
- public traces contain no secret or restricted content;
- public production has no write connector credential;
- threat model is published;
- hard gate behavior is tested.

### Evaluation

- synthetic provenance is explicit;
- split and lock files exist;
- baselines exist;
- exact counts and intervals are used;
- deterministic and live suites are separated;
- no invented human result exists;
- one genuine final-candidate failure is documented;
- public tables regenerate from raw sanitized results.

### Operations

- local Docker stack works;
- snapshot-only mode works;
- health and version routes exist;
- queue leases, retries, dead letters, and reconciliation are tested;
- telemetry and incident IDs exist;
- kill switches exist;
- zero-cost controls are enforced;
- repository plus published artifacts can restore the public snapshot experience.

### Portfolio

- stable verified public URL or an honest deployment blocker;
- clean public repository;
- working README;
- architecture diagram;
- two-minute demo asset or exact recording script;
- customer brief;
- evaluation report;
- threat model;
- runbook;
- postmortem;
- ADRs;
- no placeholders in public content;
- no secrets;
- final commit pushed.

---

## 16. Required final autonomous report

At the end, write `CODEX_FINAL_REPORT.md` and make the final Codex response concise but complete.

The report must include:

```text
Project status
Final commit SHA
Remote branch
Public URL and HTTP verification result
Local startup command
Snapshot startup command
Cohere live-run count
Cohere call cap
Confirmed billed spend
Test commands and results
GitHub Actions status
Implemented features
Deferred optional features
Known limitations
Security scan result
Secret scan result
Evaluation dataset versions
Release verdict
Exact result bundle paths
Documentation paths
Any blocker that could not be solved without a new credential or paid service
```

For spend, use only evidence available from the key/account or actual billing data.

If exact billed spend cannot be queried, write:

```text
No paid resource was created by this run. Cohere usage was restricted to the supplied zero-charge key and the configured call cap. Exact provider billing could not be independently queried.
```

Do not write `$0 billed` unless it was actually verified.

---

## 17. Start now

Begin immediately.

Do not ask me anything.

Read the PDF, inspect the repository, create the traceability and execution files, establish the zero-cost architecture, and build the complete project in the prescribed order.

Keep tests green, keep the public story honest, keep the code organized, and push stable milestones to:

```text
https://github.com/TasfiqJ/ResolveFlow.git
```

The project should be remembered for one idea:

> An enterprise agent does not deserve deployment because it produced one impressive answer. It deserves a constrained pilot only when the complete workflow—evidence access, reasoning, citations, approvals, external effects, failure recovery, and audit trail—survives reproducible replay under the conditions that matter.
