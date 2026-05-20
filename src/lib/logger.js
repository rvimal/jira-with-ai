function now() {
  return new Date().toISOString();
}

const LEVELS = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3
};

let activeLevel = LEVELS.info;

function normalizeLevel(level) {
  return String(level || "info").trim().toLowerCase();
}

function shouldLog(level) {
  return LEVELS[level] <= activeLevel;
}

function write(level, label, message, outputFn) {
  if (!shouldLog(level)) {
    return;
  }
  outputFn(`[${now()}] ${label} ${message}`);
}

export function setLogLevel(level) {
  const normalized = normalizeLevel(level);
  if (Object.hasOwn(LEVELS, normalized)) {
    activeLevel = LEVELS[normalized];
  }
}

export function logInfo(message) {
  write("info", "INFO ", message, console.log);
}

export function logWarn(message) {
  write("warn", "WARN ", message, console.warn);
}

export function logError(message) {
  write("error", "ERROR", message, console.error);
}

export function logDebug(message) {
  write("debug", "DEBUG", message, console.log);
}