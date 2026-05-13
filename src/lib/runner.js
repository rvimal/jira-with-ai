import fs from "node:fs";
import path from "node:path";
import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { loadActionDefinition } from "./actionLoader.js";
import { logInfo, logWarn } from "./logger.js";

function ensureArray(value, context) {
  if (!Array.isArray(value)) {
    throw new Error(`${context} must return an array`);
  }
  return value;
}

function normalizeTickets(rawTickets) {
  return rawTickets.map((ticket) => ({
    key: ticket.key || ticket.ticket || ticket.id,
    fields: ticket.fields || {},
    raw: ticket
  }));
}

function validateProposal(proposal, ticket, config) {
  const scoreField = config.jira.scoreField;
  const lockField = config.jira.lockField;
  const statusField = config.jira.statusField;
  const closedStatuses = new Set(config.jira.closedStatuses || []);

  if (!ticket || !ticket.key) {
    return { valid: false, reason: "Ticket not found" };
  }

  if (proposal.newValue === undefined || proposal.newValue === null) {
    return { valid: false, reason: "newValue is required" };
  }

  if (typeof proposal.newValue !== "number" || proposal.newValue < 0 || proposal.newValue > 100) {
    return { valid: false, reason: "newValue must be a number between 0 and 100" };
  }

  if (!Object.hasOwn(ticket.fields, scoreField)) {
    return { valid: false, reason: `Required field missing: ${scoreField}` };
  }

  const statusValue = ticket.fields[statusField];
  if (statusValue && closedStatuses.has(statusValue)) {
    return { valid: false, reason: "Cannot update closed ticket" };
  }

  if (lockField && ticket.fields[lockField] === true) {
    return { valid: false, reason: "Ticket is manually locked" };
  }

  return { valid: true };
}

function buildValidatedProposals(rawProposals, tickets, config) {
  const byKey = new Map(tickets.map((ticket) => [ticket.key, ticket]));
  const accepted = [];
  const rejected = [];
  const scoreField = config.jira.scoreField;

  for (const proposal of rawProposals) {
    const key = proposal.ticket;
    const ticket = byKey.get(key);
    const check = validateProposal(proposal, ticket, config);

    if (!check.valid) {
      rejected.push({ proposal, reason: check.reason });
      continue;
    }

    accepted.push({
      ticket: key,
      oldValue: ticket.fields[scoreField],
      newValue: proposal.newValue,
      reason: proposal.reason || "No reason provided"
    });
  }

  return { accepted, rejected };
}

function ensureAuditFolder(filePath) {
  const dir = path.dirname(path.resolve(process.cwd(), filePath));
  fs.mkdirSync(dir, { recursive: true });
}

function appendAuditRecord(filePath, record) {
  ensureAuditFolder(filePath);
  fs.appendFileSync(path.resolve(process.cwd(), filePath), `${JSON.stringify(record)}\n`, "utf-8");
}

function readAuditRecords(filePath) {
  const resolved = path.resolve(process.cwd(), filePath);
  if (!fs.existsSync(resolved)) {
    return [];
  }
  const lines = fs
    .readFileSync(resolved, "utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return lines.map((line) => JSON.parse(line));
}

async function confirmExecution(count) {
  const rl = readline.createInterface({ input, output });
  try {
    const answer = await rl.question(`Found ${count} updates. Proceed? (y/n) `);
    return answer.trim().toLowerCase() === "y";
  } finally {
    rl.close();
  }
}

async function applyUpdates(mcpClient, config, proposals) {
  const updates = [];
  for (const proposal of proposals) {
    const result = await mcpClient.callTool(config.mcp.tools.updateTicket, {
      key: proposal.ticket,
      fields: {
        [config.jira.scoreField]: proposal.newValue
      }
    });
    updates.push({ ticket: proposal.ticket, result });
  }
  return updates;
}

export async function runAction({ config, llmClient, mcpClient, action, mode }) {
  const runId = `${Date.now()}`;
  const startedAt = new Date().toISOString();
  const actionDef = loadActionDefinition(config.actionsDir, action);

  await mcpClient.connect();
  const tools = await mcpClient.listTools();
  logInfo(`Connected MCP tools: ${tools.map((t) => t.name).join(", ")}`);

  const fetched = await mcpClient.callTool(config.mcp.tools.fetchTickets, {
    jql: config.jira.query,
    limit: config.jira.fetchLimit
  });
  const tickets = normalizeTickets(ensureArray(fetched, "Fetch tickets tool"));

  const rawProposals = await llmClient.proposeChanges({
    systemPrompt: actionDef.system,
    instructions: actionDef.instructions,
    examples: actionDef.examples,
    tickets: tickets.map((t) => ({ key: t.key, fields: t.fields }))
  });

  const validated = buildValidatedProposals(
    ensureArray(rawProposals, "LLM output"),
    tickets,
    config
  );

  if (validated.rejected.length > 0) {
    logWarn(`Rejected ${validated.rejected.length} proposals due to guardrails`);
  }

  const baseResult = {
    action,
    mode,
    runId,
    startedAt,
    toolCount: tools.length,
    toolNames: tools.map((t) => t.name),
    fetchedTickets: tickets.length,
    proposedUpdates: validated.accepted,
    rejectedProposals: validated.rejected
  };

  if (mode === "dry-run") {
    await mcpClient.close();
    return {
      ...baseResult,
      executed: false,
      message: "Dry-run complete. No updates were applied."
    };
  }

  if (mode === "approve") {
    const ok = await confirmExecution(validated.accepted.length);
    if (!ok) {
      await mcpClient.close();
      return {
        ...baseResult,
        executed: false,
        message: "Execution cancelled by user"
      };
    }
  }

  const applyResults = await applyUpdates(mcpClient, config, validated.accepted);
  const finishedAt = new Date().toISOString();

  const auditRecord = {
    type: "execute",
    action,
    mode,
    runId,
    startedAt,
    finishedAt,
    updates: validated.accepted
  };
  appendAuditRecord(config.auditLogFile, auditRecord);

  await mcpClient.close();

  return {
    ...baseResult,
    executed: true,
    appliedCount: applyResults.length,
    applyResults
  };
}

export async function rollbackLastRun({ config, mcpClient, action }) {
  const records = readAuditRecords(config.auditLogFile)
    .filter((record) => record.type === "execute" && record.action === action)
    .sort((a, b) => (a.startedAt > b.startedAt ? -1 : 1));

  if (records.length === 0) {
    return {
      action,
      rolledBack: false,
      message: "No previous execute run found for rollback"
    };
  }

  const target = records[0];
  await mcpClient.connect();
  const tools = await mcpClient.listTools();
  logInfo(`Connected MCP tools: ${tools.map((t) => t.name).join(", ")}`);

  const rollbackResults = [];
  for (const item of target.updates || []) {
    const result = await mcpClient.callTool(config.mcp.tools.updateTicket, {
      key: item.ticket,
      fields: {
        [config.jira.scoreField]: item.oldValue
      }
    });
    rollbackResults.push({ ticket: item.ticket, oldValue: item.oldValue, result });
  }

  appendAuditRecord(config.auditLogFile, {
    type: "rollback",
    action,
    rollbackOfRunId: target.runId,
    timestamp: new Date().toISOString(),
    updates: rollbackResults.map((item) => ({
      ticket: item.ticket,
      restoredValue: item.oldValue
    }))
  });

  await mcpClient.close();

  return {
    action,
    rolledBack: true,
    rollbackOfRunId: target.runId,
    restoredCount: rollbackResults.length,
    rollbackResults
  };
}