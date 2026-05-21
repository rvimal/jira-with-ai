import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { registerRoutes } from "./routes.js";

const app = express();
const port = Number(process.env.UI_PORT || 3030);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const uiDistDir = path.join(__dirname, "public", "browser");

app.use(express.json());
app.use(express.static(uiDistDir));

registerRoutes(app);

app.get(/^(?!\/api).*/, (_req, res) => {
  res.sendFile(path.join(uiDistDir, "index.html"));
});

app.listen(port, () => {
  console.log(`UI running at http://localhost:${port}`);
});
