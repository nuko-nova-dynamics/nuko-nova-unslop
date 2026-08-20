import { preloadSchemas } from "@modelcontextprotocol/server";
import { createMcpHandler } from "agents/mcp/server";

import { createNukoNovaUnslopServer } from "./server";
import { getPrimarySkill } from "./skill-package";

preloadSchemas();

const mcpHandler = createMcpHandler(createNukoNovaUnslopServer, {
  route: "/mcp",
});

function jsonResponse(
  body: Record<string, unknown>,
  init: ResponseInit = {},
): Response {
  const headers = new Headers(init.headers);
  headers.set("content-type", "application/json; charset=utf-8");

  return new Response(JSON.stringify(body), { ...init, headers });
}

const worker = {
  async fetch(
    request: Request,
    env: unknown,
    ctx: ExecutionContext,
  ): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/mcp") {
      return mcpHandler(request, env, ctx);
    }

    if (request.method === "GET" && url.pathname === "/health") {
      const skill = getPrimarySkill();
      return jsonResponse(
        {
          ok: true,
          skillVersion: skill.version,
          sourceSha: skill.commitSha,
        },
        { headers: { "cache-control": "no-store" } },
      );
    }

    if (request.method === "GET" && url.pathname === "/") {
      const skill = getPrimarySkill();
      return jsonResponse(
        {
          name: "Nuko Nova Unslop",
          description:
            "A read-only MCP host for the Nuko Nova Unslop skill package.",
          skillVersion: skill.version,
          sourceSha: skill.commitSha,
          mcp: "/mcp",
          privacy: "This server accepts no user prose and performs no inference.",
        },
        { headers: { "cache-control": "public, max-age=300" } },
      );
    }

    return jsonResponse({ error: "Not found" }, { status: 404 });
  },
} satisfies ExportedHandler;

export default worker;
