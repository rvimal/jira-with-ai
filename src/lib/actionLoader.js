import fs from "node:fs";
import path from "node:path";

function readText(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Missing action file: ${filePath}`);
  }
  return fs.readFileSync(filePath, "utf-8");
}

export function loadActionDefinition(actionsDir, actionName) {
  const actionDir = path.resolve(process.cwd(), actionsDir, actionName);
  const systemPath = path.join(actionDir, "system.md");
  const instructionsPath = path.join(actionDir, "instructions.md");
  const examplesPath = path.join(actionDir, "examples.json");

  const system = readText(systemPath).trim();
  const instructions = readText(instructionsPath).trim();
  let examples = [];

  if (fs.existsSync(examplesPath)) {
    const raw = fs.readFileSync(examplesPath, "utf-8");
    examples = JSON.parse(raw);
  }

  return {
    actionName,
    system,
    instructions,
    examples
  };
}