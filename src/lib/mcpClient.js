import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

function normalizeToolResult(result) {
  if (!result) {
    return result;
  }

  if (result.structuredContent) {
    return result.structuredContent;
  }

  const text = result.content
    ?.filter((entry) => entry.type === "text")
    .map((entry) => entry.text)
    .join("\n");

  if (!text) {
    return result;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export function createMcpClient(config) {
  let client;
  let transport;

  return {
    async connect() {
      if (client) {
        return;
      }

      transport = new StdioClientTransport({
        command: config.mcp.command,
        args: config.mcp.args || []
      });

      client = new Client(
        {
          name: "jira-with-ai-agent",
          version: "0.1.0"
        },
        {
          capabilities: {}
        }
      );

      await client.connect(transport);
    },

    async listTools() {
      if (!client) {
        throw new Error("MCP client is not connected");
      }
      const result = await client.listTools();
      return (result.tools || []).map((tool) => ({
        name: tool.name,
        description: tool.description || ""
      }));
    },

    async callTool(name, args) {
      if (!client) {
        throw new Error("MCP client is not connected");
      }

      const result = await client.callTool({
        name,
        arguments: args || {}
      });

      return normalizeToolResult(result);
    },

    async close() {
      if (transport) {
        await transport.close();
      }
      client = null;
      transport = null;
    }
  };
}