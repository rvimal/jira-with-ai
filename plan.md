# Implementation Plan - JIRA Backlog Prioritization with LLM

This plan is designed for incremental enterprise development with validation at every step. Each phase includes:
- Build scope
- Test checklist
- Exit criteria
- Deliverables

## Phase 0 - Foundation and Working Agreements
### Goal
Freeze scope, interfaces, and operational expectations before coding.

### Tasks
1. Confirm backlog source scope:
- Project keys, board IDs, JQL filters
- Ticket volume expectations per run
2. Confirm output contract:
- Custom score field ID/name in JIRA
- Score range (0-100) and confidence range (0.0-1.0)
3. Confirm operational model:
- Daily run window and timezone
- SLA and retry policy
4. Confirm security model:
- Secret source (vault/env)
- Least-privileged API credentials

### Test Checklist
- Stakeholder sign-off on [UNDERSTANDING.md](UNDERSTANDING.md)
- Field mapping doc reviewed by product + engineering
- Security approval for secret management path

### Exit Criteria
- All assumptions from [UNDERSTANDING.md](UNDERSTANDING.md) Section 11 are validated.
- Data contract approved.

### Deliverables
- Signed-off scope notes
- Data contract document
- Environment/secrets checklist

---

## Phase 1 - Project Skeleton and Tooling
### Goal
Create production-grade Python 3.12 project skeleton with quality gates.

### Tasks
1. Create folder structure:
- app/config
- app/services
- app/prompts
- app/examples
- app/logs
- tests
2. Add dependency management and base config loading.
3. Add lint, formatting, type-check, and test runner setup.
4. Add structured logging baseline.

### Test Checklist
- Project installs cleanly in a fresh environment.
- `python --version` shows 3.12 compatibility.
- Static checks run successfully.
- Minimal smoke test passes.

### Exit Criteria
- Clean CI/local run for lint + type-check + tests.
- Standard app startup path works.

### Deliverables
- Bootstrap repository structure
- Tooling config files
- README run instructions

---

## Phase 2 - JIRA MCP Read Path (Fetch Backlog)
### Goal
Implement and verify ticket fetch pipeline from JIRA MCP.

### Tasks
1. Build MCP client adapter for authentication + requests.
2. Implement backlog fetch service with board/project filters.
3. Normalize ticket payload into internal schema.
4. Add pagination and basic rate-limit handling.

### Test Checklist
- Integration test against non-prod JIRA project.
- Verify required fields are present:
  - id, summary, description, labels, story points, priority, assignee, sprint, components, dependencies
- Pagination tested with >1 page dataset.
- Failure behavior tested (network/auth errors).

### Exit Criteria
- Fetch service returns stable normalized schema for target scope.
- Errors are handled and logged without crashing whole run.

### Deliverables
- Jira MCP client module
- Ticket normalization layer
- Read-path integration tests

---

## Phase 3 - Prompt Context Loader and Builder
### Goal
Load prompt templates/rules/examples and generate per-ticket model input.

### Tasks
1. Implement template loader from app/prompts.
2. Implement examples/rules loader from app/examples and config paths.
3. Build prompt composition service with deterministic ordering.
4. Add token budgeting strategy (truncate/summarize non-critical fields).

### Test Checklist
- Unit tests for loader behavior and missing-file handling.
- Prompt generation snapshot tests for representative tickets.
- Token size checks for small/medium/large ticket descriptions.

### Exit Criteria
- Prompt generation deterministic and version-traceable.
- Prompt stays under configured token budget threshold.

### Deliverables
- Prompt builder module
- Prompt version metadata strategy
- Unit + snapshot tests

---

## Phase 4 - LLM Gateway (GPT OSS / Qwen)
### Goal
Implement model invocation layer with provider abstraction.

### Tasks
1. Build LLM gateway interface and provider adapters.
2. Support model selection via config (GPT OSS or Qwen).
3. Add timeout, retry, and backoff policy per call.
4. Capture request/response metadata for audit (without secrets).

### Test Checklist
- Provider mock tests for success/failure/retry cases.
- Live smoke call in non-prod environment.
- Timeout behavior validated.
- Rate-limit behavior validated.

### Exit Criteria
- Gateway reliably returns raw model response and metadata.
- Failure modes are classified and observable.

### Deliverables
- LLM gateway abstraction
- Provider adapters
- Retry/backoff tests

---

## Phase 5 - Response Parser and Score Validator
### Goal
Make LLM output safe, strict, and update-ready.

### Tasks
1. Parse JSON-only response.
2. Validate required keys:
- ticket_id, score, reason, confidence
3. Validate score and confidence ranges.
4. Add fallback handling for invalid output (retry then fail-safe mark).

### Test Checklist
- Unit tests for malformed JSON, missing keys, wrong types.
- Boundary tests:
  - score at 0 and 100
  - confidence at 0.0 and 1.0
- Invalid output retry path tested.

### Exit Criteria
- Only validated responses can move to update path.
- Invalid responses are logged and safely quarantined.

### Deliverables
- Parser/validator module
- Schema tests and edge-case tests

---

## Phase 6 - JIRA MCP Write Path (Update Custom Field)
### Goal
Implement reliable and idempotent score update into JIRA.

### Tasks
1. Build custom field update API through Jira MCP.
2. Add idempotency check (skip if same score already present).
3. Add per-ticket status recording: updated/skipped/failed.
4. Add retry policy for transient update failures.

### Test Checklist
- Integration test updates score in non-prod issue.
- Verify no-op behavior when score unchanged.
- Verify duplicate update prevention.
- Verify transient failure retry and final status recording.

### Exit Criteria
- Score writes are correct, traceable, and non-duplicative.

### Deliverables
- Update service module
- Idempotency logic
- Write-path integration tests

---

## Phase 7 - End-to-End Orchestration
### Goal
Wire full flow for ticket batch execution.

### Tasks
1. Build orchestrator flow:
- fetch -> prompt -> llm -> parse/validate -> update -> audit
2. Add batch controls:
- max tickets per run
- configurable concurrency
- partial-failure continuation
3. Add final run summary report.

### Test Checklist
- E2E run with mixed ticket quality and expected failures.
- Verify counts:
- total, success, failed, retried, skipped
- Verify run continues despite individual ticket failures.

### Exit Criteria
- One command executes complete run and returns deterministic summary.

### Deliverables
- Orchestrator service
- E2E test scenario pack
- Run summary output format

---

## Phase 8 - Scheduling and Operations
### Goal
Automate daily execution and operational visibility.

### Tasks
1. Implement scheduler mode:
- Linux cron and/or APScheduler mode
2. Add job lock to avoid overlapping runs.
3. Add alerting hooks for failed runs.
4. Add log rotation and retention policy.

### Test Checklist
- Dry-run scheduled execution test.
- Overlap protection test (second run blocked if first active).
- Alert triggers on synthetic failure.
- Log retention policy verified.

### Exit Criteria
- Stable unattended daily execution in non-prod.

### Deliverables
- Scheduler configuration
- Ops runbook
- Alert policy documentation

---

## Phase 9 - Security, Compliance, and Observability Hardening
### Goal
Meet enterprise readiness standards.

### Tasks
1. Secret handling audit (no hardcoded credentials).
2. Add structured logs with correlation IDs.
3. Add metrics dashboard and SLO signals.
4. Add immutable audit trail for scoring decisions.

### Test Checklist
- Secret scan passes.
- Log schema validated in centralized log pipeline.
- Metrics emitted for each major stage.
- Audit records reproducible from stored metadata.

### Exit Criteria
- Security and observability controls pass enterprise review.

### Deliverables
- Security checklist evidence
- Logging/metrics schema docs
- Audit trail design note

---

## Phase 10 - Deployment and Release
### Goal
Package and release for enterprise operations.

### Tasks
1. Containerize app (Dockerfile + runtime config).
2. Prepare deployment variants:
- Linux cron host
- Jenkins scheduled pipeline
- Kubernetes CronJob
3. Add environment-specific config templates.
4. Execute staged rollout: dev -> qa -> prod.

### Test Checklist
- Container image build and run smoke test.
- Jenkins schedule test.
- Kubernetes CronJob test with secret injection.
- Rollback drill validated.

### Exit Criteria
- Production deployment approved with rollback plan and monitoring active.

### Deliverables
- Deployment manifests/pipeline definitions
- Release checklist
- Go-live runbook

---

## Continuous Test Strategy (Across All Phases)
1. Unit tests for all pure logic modules.
2. Integration tests for Jira MCP + LLM gateway adapters.
3. Contract tests for request/response schemas.
4. E2E tests for daily batch workflow.
5. Resilience tests for timeout, rate-limit, and partial outage scenarios.

## Suggested Milestone Gate Reviews
1. Gate A (after Phase 2): Jira read-path readiness
2. Gate B (after Phase 5): LLM safety and schema reliability
3. Gate C (after Phase 7): End-to-end functional readiness
4. Gate D (after Phase 9): Enterprise hardening readiness
5. Gate E (after Phase 10): Production go-live approval

## Progress Tracking Template
Use this at the end of each sprint/day:

- Planned phase:
- Completed tasks:
- Tests executed:
- Passed:
- Failed:
- Risks/Blockers:
- Decision needed:
- Next phase start date:

## Recommended First Sprint (Practical Start)
1. Complete Phase 0 and Phase 1.
2. Implement Phase 2 read path for a single project filter.
3. Add 3 integration tests:
- successful fetch
- auth failure
- pagination behavior
4. Demo output as normalized ticket JSON and run summary.
