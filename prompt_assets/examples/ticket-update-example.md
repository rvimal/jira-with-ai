Input ticket summary:

- summary: Investigate payment timeout
- description: Customer reports intermittent payment gateway timeouts.

Expected response:

{
  "update": {
    "fields": {
      "priority": "High",
      "labels": ["llm-reviewed", "needs-investigation"]
    }
  },
  "reason": "Payment issues affect customer transactions and need prompt triage."
}