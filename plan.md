Implement the below,

- Use node.js
- for connecting to MCP use @modelcontextprotocol npm
- do not write unit test
- keep the code very simple 
- Url, model, token and certificate should e configurable
- MCP also configurable 
- Target the LLM implemenation for GPT-OSS and Qwen model
- MCP should be connect and list all the avaiable tools before execution 
- there should option to run each implemation for example test LLM and test MCP sepratly 


What you're building becomes a **Human-configured Agent Platform** where:

* Platform provides execution framework
* Users provide business intelligence through prompts
* LLM performs reasoning
* Agent executes through MCP
* Users validate before production rollout

That’s a strong enterprise model.

## Updated design understanding

Your platform responsibility:

### 1. Runtime engine

The platform handles:

* Secure LLM connection (token + certificate)
* MCP connection to Jira
* Loading action prompts from folders
* Scheduling
* Execution
* Logging
* Dry-run

---

### 2. User responsibility

Users define:

* Business action name
* Prompt instructions
* Examples
* Expected behavior

Example:

```text id="j7m1fq"
actions/risk/
```

Contains:

* system.md
* instructions.md
* examples.json

If prompt quality is poor → output quality may be poor.

That’s acceptable if your platform clearly documents this ownership.

---

# Dry run is mandatory here

Since the LLM decides scoring/action, dry run becomes critical.

Example:

```bash id="vcwgut"
agent run --action risk --dry-run
```

Dry run should:

## Step 1

Fetch Jira tickets via MCP

## Step 2

Send prompt + ticket data to LLM

## Step 3

Show proposed changes only

Example:

```json id="zx2k5r"
[
  {
    "ticket": "ABC-101",
    "oldValue": null,
    "newValue": 82,
    "reason": "High complexity with blocker dependencies"
  }
]
```

## Step 4

No updates performed.

---

# Production mode

```bash id="e4j8qk"
agent run --action risk --execute
```

Only after dry-run validation.

---

# Even better: approval mode

Instead of immediately updating:

```bash id="0jxkqo"
agent run --action risk --approve
```

Output:

```text id="jl3jlwm"
Found 34 updates.
Proceed? (y/n)
```

Very useful in enterprise environments.

---

# Recommended modes

Your CLI should support:

| Mode         | Purpose                 |
| ------------ | ----------------------- |
| `--dry-run`  | Preview changes         |
| `--execute`  | Apply changes           |
| `--schedule` | Automated execution     |
| `--rollback` | Revert previous updates |

Rollback is extremely useful if an action prompt behaves unexpectedly.

---

# One thing I’d strongly add

Even if prompt ownership belongs to users, platform should still enforce **guardrails**:

Example validations:

* Score must be within allowed range
* Required Jira fields must exist
* Cannot update closed tickets
* Cannot overwrite manually locked values

This protects Jira from bad prompts.

---

So your final design becomes:

```text id="otjlwm"
User Prompt
    ↓
Agent CLI
    ↓
LLM Reasoning
    ↓
Dry Run Validation
    ↓
Approval / Scheduler
    ↓
MCP Update to Jira
    ↓
Audit Logs
```


