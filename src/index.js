#!/usr/bin/env node

import { loadConfig } from "./lib/config.js";
import { createLlmClient } from "./lib/llmClient.js";
import { createMcpClient } from "./lib/mcpClient.js";
import { runAction, rollbackLastRun } from "./lib/runner.js";
import { logInfo, logError } from "./lib/logger.js";

function parseArgs(argv) {
  const args = [...argv];
  const command = args.shift();
  const options = {};

  while (args.length > 0) {
    const current = args.shift();

    if (!current.startsWith("--")) {
      continue;
    }

    const key = current.slice(2);
    const next = args[0];
    if (!next || next.startsWith("--")) {
      options[key] = true;
    } else {
      options[key] = args.shift();
    }
  }

  return { command, options };
}

function modeFromOptions(options) {
  if (options.rollback) {
    return "rollback";
  }
  if (options.execute) {
    return "execute";
  }
  if (options.approve) {
    return "approve";
  }
  return "dry-run";
}

function printUsage() {
  console.log(`
Usage:
  agent test-llm
  agent test-mcp
  agent run --action <name> [--dry-run|--execute|--approve] [--schedule] [--interval-ms <ms>] [--rollback]

Examples:
  agent test-llm
  agent test-mcp
  agent run --action risk --dry-run
  agent run --action risk --approve
  agent run --action risk --execute
  agent run --action risk --execute --schedule --interval-ms 600000
  agent run --action risk --rollback
`);
}

async function runScheduled(task, intervalMs) {
  await task();
  logInfo(`Schedule enabled. Next run every ${intervalMs} ms.`);
  setInterval(async () => {
    try {
      await task();
    } catch (error) {
      logError(`Scheduled run failed: ${error.message}`);
    }
  }, intervalMs);
}

async function main() {
  const { command, options } = parseArgs(process.argv.slice(2));
  const config = loadConfig();

  if (!command || command === "--help" || command === "-h" || options.help) {
    printUsage();
    process.exit(0);
  }

  const llmClient = createLlmClient(config);
  const mcpClient = createMcpClient(config);

  if (command === "test-llm") {
    const result = await llmClient.testConnection();
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  if (command === "test-mcp") {
    await mcpClient.connect();
    const tools = await mcpClient.listTools();
    console.log(JSON.stringify({ connected: true, tools }, null, 2));
    await mcpClient.close();
    return;
  }

  if (command === "run") {
    const action = options.action;
    if (!action) {
      throw new Error("Missing --action argument");
    }

    const mode = modeFromOptions(options);
    if (mode === "rollback") {
      const result = await rollbackLastRun({ config, mcpClient, action });
      console.log(JSON.stringify(result, null, 2));
      return;
    }

    const task = async () => {
      const result = await runAction({
        config,
        llmClient,
        mcpClient,
        action,
        mode
      });
      console.log(JSON.stringify(result, null, 2));
    };

    if (options.schedule) {
      const intervalMs = Number(options["interval-ms"] || config.scheduleIntervalMs || 300000);
      await runScheduled(task, intervalMs);
      return;
    }

    await task();
    return;
  }

  throw new Error(`Unknown command: ${command}`);
}

main().catch((error) => {
  logError(error.message);
  process.exit(1);
});