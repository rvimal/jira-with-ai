# JIRA Backlog Prioritization with LLM - Requirement Understanding

## 1) Objective
Build an enterprise-grade, Python 3.12 compatible solution that runs daily and automatically prioritizes JIRA backlog tickets by calculating a custom Priority Score using an LLM (GPT OSS or Qwen), then updates that score back into JIRA through JIRA MCP integration.

This document captures requirement understanding, architecture intent, operating model, and delivery expectations. It does not include code implementation.

Default operating cadence is **daily**. Any alternate frequency (for example hourly) is a configurable operational override and not the baseline requirement.

## 2) Business Outcome
- Reduce manual backlog triage effort for product and engineering teams.
- Improve consistency and transparency of prioritization decisions.
- Provide traceable, explainable score and reasoning for each ticket.
- Enable daily refresh of backlog priority based on latest ticket metadata.

## 3) Scope Understanding
### In Scope
- Daily automated workflow (scheduler-driven).
- Fetch backlog tickets from selected JIRA projects/boards via JIRA MCP.
- Read ticket attributes used in scoring:
  - Ticket ID
  - Summary
  - Description
  - Labels
  - Story Points
  - Priority
  - Assignee
  - Sprint
  - Components
  - Dependencies
- Use enterprise prompt/rule/example artifacts as scoring context.
- Invoke GPT OSS or Qwen to produce score, confidence, and rationale.
- Validate output and update JIRA custom score field via MCP.
- Logging, retries, and robust error handling.
- Secure secrets/config handling and deployable runtime model.

### Out of Scope (for current request)
- Full production code delivery in this step.
- UI/dashboard development.
- Human approval workflow design (unless explicitly added later).

## 4) End-to-End Process Understanding
1. Scheduler triggers daily job (default cadence).
2. Job authenticates and connects to JIRA MCP.
3. Backlog tickets are fetched based on configured board/project filters.
4. Prompt builder combines:
   - Ticket data
   - Formula/rules document
   - Prompt templates
   - Example files
5. LLM service (GPT OSS/Qwen) is called.
6. LLM returns structured JSON (ticket_id, score, reason, confidence).
7. Response parser and validator enforce schema and score constraints.
8. If valid, score is written to JIRA custom field via MCP.
9. Processing audit is logged per ticket.
10. Failures are retried per policy; unrecoverable failures are reported.

Additional runtime behaviors:
- If computed score is unchanged from existing custom field value, skip update and log as idempotent no-op.
- If LLM output is invalid after retry policy, mark ticket as failed with reason code and continue batch processing.
- Persist run-level summary: total tickets, success, failed, retried, skipped, and execution duration.

## 5) Target Architecture (Conceptual)

+--------------------------+
| Scheduler                |
| Cron / APScheduler       |
+------------+-------------+
             |
             v
+--------------------------+
| Python Orchestrator      |
| Job Runner / Workflow    |
+---+------------------+---+
    |                  |
    v                  v
+----------+      +----------------+
| JIRA MCP |<---->| Ticket Service |
| Client   |      +----------------+
+----+-----+               |
     |                     v
     |              +------------------+
     |              | Prompt Builder   |
     |              | Rules + Examples |
     |              +---------+--------+
     |                        |
     |                        v
     |              +------------------+
     |              | LLM Gateway      |
     |              | GPT OSS / Qwen   |
     |              +---------+--------+
     |                        |
     |                        v
     |              +------------------+
     |              | Validator/Parser |
     |              +---------+--------+
     |                        |
     +<-----------------------+
              update score

Cross-cutting: logging, retries, exception handling, metrics, security, idempotency controls.

### 5.1) Architecture Conformance Checklist (for Diagram/Implementation Reviews)
The architecture is considered aligned only if all below are represented:
- Scheduler shown as daily baseline trigger.
- Python orchestrator/job runner.
- Jira MCP integration path for both fetch and update.
- Prompt/rules/examples context loading.
- LLM gateway supporting GPT OSS **and/or** Qwen.
- Explicit response parser/validator before Jira update.
- Authentication/secret handling path for external systems.
- Cross-cutting controls: logging, retry, exception handling, metrics, security, idempotency.

## 6) Enterprise Non-Functional Requirements (Interpreted)
- Reliability: controlled retries, dead-letter/error reporting, graceful degradation.
- Scalability: batch processing and configurable concurrency.
- Performance: token-efficient prompt design and bounded runtime per batch.
- Security: secret vault/env-based credentials, least privilege, encrypted transport.
- Observability: structured logs, metrics, run-level and ticket-level audit trail.
- Compliance: deterministic update rules, traceable model inputs/outputs.
- Maintainability: modular architecture and clear separation of concerns.

## 7) Prompt Engineering Expectations
The scoring prompt should combine business dimensions with explicit scoring guidance:
- Business impact
- Complexity
- Revenue impact
- Customer urgency
- Risk
- Dependency count
- Delivery effort
- Strategic importance

Expected strict JSON output:
{
  "ticket_id": "",
  "score": 0,
  "reason": "",
  "confidence": 0
}

Understanding notes:
- JSON-only response should be enforced.
- Recommended default boundaries:
  - score: integer in range 0-100
  - confidence: float in range 0.0-1.0
- Rationale should be concise and auditable.

## 8) Data and Decision Governance
- Inputs to score should be reproducible from ticket snapshot + rules version.
- Output updates should include trace context (job id, model id, prompt version).
- Idempotency required to avoid duplicate/unnecessary updates.
- Hallucination control required through schema checks and defensive validation.
- Duplicate update prevention should compare existing vs new score before write.
- Store immutable audit records for model request/response metadata (excluding sensitive secrets).

## 9) Deployment Options (Expected Recommendations)
- Linux Cron:
  - Lightweight host-level scheduling for smaller deployments.
- Jenkins Scheduler:
  - Centralized enterprise CI/CD-driven scheduling and governance.
- Kubernetes CronJob:
  - Cloud-native scheduling with scaling, restart policies, and secret injection.
- Docker Container:
  - Portable runtime packaging for all above environments.

## 10) Expected Final Deliverables (From Future Implementation Phase)
- Architecture diagram (ASCII).
- Step-by-step technical explanation.
- Complete modular Python codebase.
- LLM prompt template and supporting examples.
- Scheduler setup guide.
- Deployment guide for cron/Jenkins/K8s/Docker.
- Production best-practices checklist.

## 11) Key Assumptions to Validate
- JIRA MCP supports both read (backlog fetch) and write (custom field update).
- Custom score field exists and is writable for target projects.
- Prompt/rules/examples are versioned and accessible at runtime.
- GPT OSS/Qwen endpoint is enterprise-approved and reachable.
- Daily job window and SLA are defined.
- Credential source (vault or environment-injected secret) is approved by enterprise security.

## 12) Risks Identified Early
- Inconsistent ticket data quality can reduce scoring reliability.
- Rate limits from JIRA MCP or LLM endpoints can delay runs.
- Model output variability may require strict guardrails and fallback logic.
- Excessive token usage can increase cost and latency.
- Missing governance for rule changes can impact score consistency.

## 13) Acceptance Criteria (Understanding Baseline)
- Daily run completes and processes configured backlog scope.
- Each processed ticket yields valid score JSON (or tracked failure state).
- JIRA custom score updates are successful, traceable, and non-duplicative.
- Logs and audit records support post-run review.
- Deployment pattern is documented for cron, Jenkins, Kubernetes, and Docker.

## 14) Next Implementation Phase (Suggested)
- Confirm score formula ranges, confidence thresholds, and fallback policy.
- Finalize data contracts (JIRA fields, MCP payloads, LLM schema).
- Build modular Python services and integration adapters.
- Add integration tests, resiliency tests, and operational runbooks.
