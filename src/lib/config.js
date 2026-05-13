import fs from "node:fs";
import path from "node:path";

function deepMerge(base, override) {
  const output = { ...base };
  for (const [key, value] of Object.entries(override || {})) {
    if (value === undefined) {
      continue;
    }
    if (
      value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      typeof output[key] === "object" &&
      output[key] !== null
    ) {
      output[key] = deepMerge(output[key], value);
    } else {
      output[key] = value;
    }
  }
  return output;
}

function readJsonFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return null;
  }
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw);
}

export function loadConfig() {
  const cwd = process.cwd();
  const defaultPath = path.join(cwd, "config", "default.json");
  const localPath = process.env.AGENT_CONFIG
    ? path.resolve(cwd, process.env.AGENT_CONFIG)
    : path.join(cwd, "config", "local.json");

  let config = readJsonFile(defaultPath) || {};
  const localConfig = readJsonFile(localPath) || {};
  config = deepMerge(config, localConfig);

  const envOverride = {
    llm: {
      url: process.env.LLM_URL,
      model: process.env.LLM_MODEL,
      token: process.env.LLM_TOKEN,
      caFile: process.env.LLM_CA_FILE,
      certFile: process.env.LLM_CERT_FILE,
      keyFile: process.env.LLM_KEY_FILE,
      insecureSkipTlsVerify: process.env.LLM_INSECURE
        ? process.env.LLM_INSECURE === "true"
        : undefined
    },
    mcp: {
      command: process.env.MCP_COMMAND,
      args: process.env.MCP_ARGS ? process.env.MCP_ARGS.split(",") : undefined,
      tools: {
        fetchTickets: process.env.MCP_FETCH_TOOL,
        updateTicket: process.env.MCP_UPDATE_TOOL
      }
    },
    actionsDir: process.env.ACTIONS_DIR,
    auditLogFile: process.env.AUDIT_LOG_FILE
  };

  config = deepMerge(config, envOverride);

  if (!config.llm?.url) {
    throw new Error("LLM URL is required. Set config.llm.url or LLM_URL.");
  }
  if (!config.llm?.model) {
    throw new Error("LLM model is required. Set config.llm.model or LLM_MODEL.");
  }
  if (!config.mcp?.command) {
    throw new Error("MCP command is required. Set config.mcp.command or MCP_COMMAND.");
  }

  return config;
}