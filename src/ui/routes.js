import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { loadConfig } from "../lib/config.js";

let running = false;
const ACTION_FILES = new Set(["system.md", "instructions.md", "examples.json"]);
const ACTION_NAME_RE = /^[A-Za-z0-9_-]+$/;

function repoPath(...parts) {
  return path.resolve(process.cwd(), ...parts);
}

function getActionsRoot() {
  return repoPath("actions");
}

function assertActionName(action) {
  if (!ACTION_NAME_RE.test(action)) {
    throw new Error("Invalid action name. Use letters, numbers, dash, underscore only.");
  }
}

function resolveActionDir(action) {
  assertActionName(action);
  const root = getActionsRoot();
  const dir = path.resolve(root, action);
  const relative = path.relative(root, dir);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Invalid action path");
  }
  return dir;
}

function assertActionFile(fileName) {
  if (!ACTION_FILES.has(fileName)) {
    throw new Error(`Unsupported file: ${fileName}`);
  }
}

function readFileIfExists(filePath) {
  if (!fs.existsSync(filePath)) {
    return "";
  }
  return fs.readFileSync(filePath, "utf-8");
}

function readActionPayload(action) {
  const actionDir = resolveActionDir(action);

  return {
    action,
    files: {
      "system.md": readFileIfExists(path.join(actionDir, "system.md")),
      "instructions.md": readFileIfExists(path.join(actionDir, "instructions.md")),
      "examples.json": readFileIfExists(path.join(actionDir, "examples.json"))
    }
  };
}

function readTail(filePath, maxLines = 200) {
  if (!fs.existsSync(filePath)) {
    return [];
  }
  const lines = fs.readFileSync(filePath, "utf-8").split("\n").filter(Boolean);
  return lines.slice(-maxLines);
}

function runAgentCommand(args) {
  return new Promise((resolve) => {
    const child = spawn("npm", ["run", "agent", "--", ...args], {
      cwd: process.cwd(),
      shell: true
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("close", (code) => {
      resolve({
        code,
        stdout,
        stderr
      });
    });
  });
}

async function runWithLock(res, args) {
  if (running) {
    res.status(409).json({ error: "Another run is already in progress" });
    return;
  }

  running = true;
  try {
    const result = await runAgentCommand(args);
    res.json(result);
  } finally {
    running = false;
  }
}

export function registerRoutes(app) {
  app.get("/api/config", (_req, res) => {
    try {
      const config = loadConfig();
      res.json({
        llm: {
          url: config.llm?.url || "",
          model: config.llm?.model || "",
          tokenConfigured: Boolean(config.llm?.token),
          insecureSkipTlsVerify: Boolean(config.llm?.insecureSkipTlsVerify),
          temperature: Number(config.llm?.temperature ?? 0.1)
        },
        mcp: {
          command: config.mcp?.command || "",
          args: config.mcp?.args || [],
          tools: {
            fetchTickets: config.mcp?.tools?.fetchTickets || "",
            updateTicket: config.mcp?.tools?.updateTicket || ""
          }
        },
        jira: {
          project: config.jira?.project || "",
          query: config.jira?.query || "",
          fetchLimit: Number(config.jira?.fetchLimit ?? 0)
        },
        actionsDir: config.actionsDir || "./actions",
        auditLogFile: config.auditLogFile || "./logs/audit.jsonl",
        scheduleIntervalMs: Number(config.scheduleIntervalMs ?? 300000),
        logLevel: config.logLevel || "info"
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/status", (_req, res) => {
    res.json({ running });
  });

  app.get("/api/actions", (_req, res) => {
    const actionsRoot = getActionsRoot();
    const actions = fs.existsSync(actionsRoot)
      ? fs
          .readdirSync(actionsRoot, { withFileTypes: true })
          .filter((entry) => entry.isDirectory())
          .map((entry) => entry.name)
      : [];

    res.json({ actions });
  });

  app.get("/api/actions/:action", (req, res) => {
    try {
      const action = String(req.params.action || "").trim();
      const actionDir = resolveActionDir(action);
      if (!fs.existsSync(actionDir)) {
        res.status(404).json({ error: `Action not found: ${action}` });
        return;
      }
      res.json(readActionPayload(action));
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  });

  app.post("/api/actions", (req, res) => {
    try {
      const action = String(req.body?.action || "").trim();
      const systemText = String(req.body?.system || "").trim();
      const instructionsText = String(req.body?.instructions || "").trim();

      assertActionName(action);
      if (!systemText || !instructionsText) {
        res.status(400).json({ error: "system and instructions are required" });
        return;
      }

      const actionDir = resolveActionDir(action);
      if (fs.existsSync(actionDir)) {
        res.status(409).json({ error: `Action already exists: ${action}` });
        return;
      }

      fs.mkdirSync(actionDir, { recursive: true });
      fs.writeFileSync(path.join(actionDir, "system.md"), `${systemText}\n`, "utf-8");
      fs.writeFileSync(path.join(actionDir, "instructions.md"), `${instructionsText}\n`, "utf-8");
      fs.writeFileSync(path.join(actionDir, "examples.json"), "[]\n", "utf-8");

      res.status(201).json(readActionPayload(action));
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  });

  app.put("/api/actions/:action/files/:fileName", (req, res) => {
    try {
      const action = String(req.params.action || "").trim();
      const fileName = String(req.params.fileName || "").trim();
      const content = String(req.body?.content || "");

      const actionDir = resolveActionDir(action);
      assertActionFile(fileName);

      if (!fs.existsSync(actionDir)) {
        res.status(404).json({ error: `Action not found: ${action}` });
        return;
      }

      if (fileName === "examples.json") {
        JSON.parse(content || "[]");
      }

      fs.writeFileSync(path.join(actionDir, fileName), content, "utf-8");
      res.json({ ok: true, action, fileName });
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  });

  app.post("/api/run/test-llm", async (_req, res) => {
    await runWithLock(res, ["test-llm"]);
  });

  app.post("/api/run/test-mcp", async (_req, res) => {
    await runWithLock(res, ["test-mcp"]);
  });

  app.post("/api/run/execute", async (req, res) => {
    const action = String(req.body?.action || "").trim();
    if (!action) {
      res.status(400).json({ error: "action is required" });
      return;
    }

    const actionPath = repoPath("actions", action);
    if (!fs.existsSync(actionPath)) {
      res.status(400).json({ error: `Unknown action: ${action}` });
      return;
    }

    await runWithLock(res, ["run", "--action", action, "--execute"]);
  });

  app.post("/api/run/action", async (req, res) => {
    const action = String(req.body?.action || "").trim();
    const mode = String(req.body?.mode || "dry-run").trim();

    if (!action) {
      res.status(400).json({ error: "action is required" });
      return;
    }

    const actionPath = repoPath("actions", action);
    if (!fs.existsSync(actionPath)) {
      res.status(400).json({ error: `Unknown action: ${action}` });
      return;
    }

    const modeArg =
      mode === "execute"
        ? "--execute"
        : mode === "approve"
          ? "--approve"
          : "--dry-run";

    await runWithLock(res, ["run", "--action", action, modeArg]);
  });

  app.get("/api/logs/scheduler", (_req, res) => {
    const lines = readTail(repoPath("logs", "scheduler-audit.log"), 400);
    res.json({ lines });
  });

  app.get("/api/logs/audit", (_req, res) => {
    const lines = readTail(repoPath("logs", "audit.jsonl"), 400);
    res.json({ lines });
  });
}
