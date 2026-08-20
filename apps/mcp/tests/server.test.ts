import { Client, InMemoryTransport } from "@modelcontextprotocol/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { z } from "zod";

import { createNukoNovaUnslopServer } from "../src/server";

const skillResourceSchema = z.object({
  uri: z.string(),
  digest: z.string(),
});

const skillEntrySchema = z.object({
  uri: z.string(),
  frontmatter: z.record(z.string(), z.string()),
  resources: z.array(skillResourceSchema),
});

const skillsListResultSchema = z.object({
  skills: z.array(skillEntrySchema),
  nextCursor: z.string().optional(),
});

const skillGetResultSchema = z.object({
  skill: skillEntrySchema,
});

describe("Nuko Nova Unslop MCP server", () => {
  let client: Client;
  let server: ReturnType<typeof createNukoNovaUnslopServer>;

  beforeEach(async () => {
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    client = new Client({ name: "nuko-nova-unslop-test", version: "1.0.0" });
    server = createNukoNovaUnslopServer();

    await Promise.all([
      server.connect(serverTransport),
      client.connect(clientTransport),
    ]);
  });

  afterEach(async () => {
    await Promise.allSettled([client.close(), server.close()]);
  });

  it("advertises the OpenAI skills extension and read-only instructions", () => {
    expect(client.getServerCapabilities()?.extensions).toEqual({
      "io.modelcontextprotocol/skills": {},
    });
    expect(client.getInstructions()).toContain("never accepts user prose");
    expect(client.getInstructions()).toContain("invokes Unslop");
  });

  it("exposes the complete skill through skills/list and skills/get", async () => {
    const listResult = await client.request(
      { method: "skills/list", params: {} },
      skillsListResultSchema,
    );
    const entry = listResult.skills[0];

    expect(listResult.skills).toHaveLength(1);
    expect(entry?.frontmatter.name).toBe("nuko-nova-unslop");
    expect(entry?.resources.length).toBeGreaterThan(5);

    const getResult = await client.request(
      { method: "skills/get", params: { uri: entry?.uri } },
      skillGetResultSchema,
    );

    expect(getResult.skill).toEqual(entry);
  });

  it("returns every declared skill resource with matching text", async () => {
    const listResult = await client.request(
      { method: "skills/list", params: {} },
      skillsListResultSchema,
    );
    const primaryResource = listResult.skills[0]?.resources.find((resource) =>
      resource.uri.endsWith("/SKILL.md"),
    );

    expect(primaryResource).toBeDefined();

    const result = await client.readResource({ uri: primaryResource!.uri });

    expect(result.contents).toHaveLength(1);
    expect(result.contents[0]?.uri).toBe(primaryResource?.uri);
    expect(result.contents[0]).toMatchObject({
      mimeType: "text/markdown",
      text: expect.stringContaining("# Nuko Nova Unslop"),
    });
  });

  it("offers only package-loading tools and accepts no writing input", async () => {
    const { tools } = await client.listTools();

    expect(tools.map((tool) => tool.name)).toEqual([
      "load_nuko_nova_unslop",
      "read_nuko_nova_reference",
    ]);
    expect(tools[0]?.annotations).toMatchObject({
      readOnlyHint: true,
      destructiveHint: false,
      openWorldHint: false,
    });
    expect(tools[0]?.inputSchema).toMatchObject({
      type: "object",
      properties: {},
      additionalProperties: false,
    });
    expect(JSON.stringify(tools)).not.toContain("text_to_rewrite");
    expect(JSON.stringify(tools)).not.toContain("user_prose");
    expect(tools[0]?.title).toBe("Load Unslop");
    expect(tools[0]?.description).toContain("@Unslop");
  });

  it("loads the standard and allows only named package references", async () => {
    const loaded = await client.callTool({
      name: "load_nuko_nova_unslop",
      arguments: {},
    });

    expect(loaded.isError).not.toBe(true);
    expect(loaded.content[0]).toMatchObject({
      type: "text",
      text: expect.stringContaining("# Nuko Nova Unslop"),
    });

    const rejected = await client.callTool({
      name: "read_nuko_nova_reference",
      arguments: { name: "../../AGENTS.md" },
    });

    expect(rejected.isError).toBe(true);
  });
});
