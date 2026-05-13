import fs from "node:fs";
import https from "node:https";
import axios from "axios";

function createHttpsAgent(llmConfig) {
  const options = {
    rejectUnauthorized: !llmConfig.insecureSkipTlsVerify
  };

  if (llmConfig.caFile) {
    options.ca = fs.readFileSync(llmConfig.caFile, "utf-8");
  }
  if (llmConfig.certFile) {
    options.cert = fs.readFileSync(llmConfig.certFile, "utf-8");
  }
  if (llmConfig.keyFile) {
    options.key = fs.readFileSync(llmConfig.keyFile, "utf-8");
  }

  return new https.Agent(options);
}

function buildMessages(payload) {
  return [
    { role: "system", content: payload.systemPrompt },
    {
      role: "user",
      content: [
        payload.instructions,
        "",
        "Examples:",
        JSON.stringify(payload.examples || [], null, 2),
        "",
        "Tickets:",
        JSON.stringify(payload.tickets || [], null, 2),
        "",
        "Return only JSON array format:",
        "[{\"ticket\":\"ABC-1\",\"newValue\":60,\"reason\":\"...\"}]"
      ].join("\n")
    }
  ];
}

function extractJsonArray(text) {
  const start = text.indexOf("[");
  const end = text.lastIndexOf("]");
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("LLM response does not contain a JSON array");
  }
  const candidate = text.slice(start, end + 1);
  return JSON.parse(candidate);
}

export function createLlmClient(config) {
  const llmConfig = config.llm;
  const baseUrl = llmConfig.url.replace(/\/$/, "");

  const http = axios.create({
    baseURL: baseUrl,
    timeout: 60000,
    httpsAgent: createHttpsAgent(llmConfig),
    headers: llmConfig.token
      ? {
          Authorization: `Bearer ${llmConfig.token}`
        }
      : {}
  });

  return {
    async testConnection() {
      const response = await http.post("/chat/completions", {
        model: llmConfig.model,
        temperature: 0,
        messages: [
          {
            role: "user",
            content: "Reply with exactly: LLM_OK"
          }
        ]
      });

      return {
        model: llmConfig.model,
        status: "ok",
        output: response.data?.choices?.[0]?.message?.content || null
      };
    },

    async proposeChanges(payload) {
      const response = await http.post("/chat/completions", {
        model: llmConfig.model,
        temperature: llmConfig.temperature ?? 0.1,
        messages: buildMessages(payload)
      });

      const content = response.data?.choices?.[0]?.message?.content;
      if (!content || typeof content !== "string") {
        throw new Error("LLM returned empty response");
      }
      return extractJsonArray(content);
    }
  };
}