import { describe, expect, it } from "vitest";

import worker from "../src/index";

const executionContext = {
  passThroughOnException() {},
  waitUntil() {},
} as unknown as ExecutionContext;

describe("Cloudflare Worker edge", () => {
  it("describes the public read-only endpoint", async () => {
    const response = await worker.fetch(
      new Request("https://unslop.example.test/"),
      {},
      executionContext,
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toContain("public");
    await expect(response.json()).resolves.toMatchObject({
      name: "Nuko Nova Unslop",
      mcp: "/mcp",
      privacy: "This server accepts no user prose and performs no inference.",
    });
  });

  it("provides a health check and rejects unknown routes", async () => {
    const health = await worker.fetch(
      new Request("https://unslop.example.test/health"),
      {},
      executionContext,
    );
    const missing = await worker.fetch(
      new Request("https://unslop.example.test/unknown"),
      {},
      executionContext,
    );

    expect(health.status).toBe(200);
    await expect(health.json()).resolves.toMatchObject({ ok: true });
    expect(missing.status).toBe(404);
  });

  it("handles MCP initialization at the single public route", async () => {
    const response = await worker.fetch(
      new Request("https://unslop.example.test/mcp", {
        method: "POST",
        headers: {
          accept: "application/json, text/event-stream",
          "content-type": "application/json",
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "initialize",
          params: {
            protocolVersion: "2025-11-25",
            capabilities: {},
            clientInfo: { name: "worker-test", version: "1.0.0" },
          },
        }),
      }),
      {},
      executionContext,
    );

    expect(response.status).toBe(200);
    const body = await response.text();
    expect(body).toContain("nuko-nova-unslop");
    expect(body).toContain("io.modelcontextprotocol/skills");
  });
});
