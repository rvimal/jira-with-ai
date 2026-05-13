function now() {
  return new Date().toISOString();
}

export function logInfo(message) {
  console.log(`[${now()}] INFO  ${message}`);
}

export function logWarn(message) {
  console.warn(`[${now()}] WARN  ${message}`);
}

export function logError(message) {
  console.error(`[${now()}] ERROR ${message}`);
}