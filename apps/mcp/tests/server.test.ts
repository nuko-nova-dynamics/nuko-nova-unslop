import { Client, InMemoryTransport } from "@modelcontextprotocol/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { z } from "zod";

import { createNukoNovaUnslopServer } from "../src/server";
import { getPrimarySkill, getReference, getSkillCatalog, getSuperTightenSkill, listAllSkillResources } from "../src/skill-package";
import { sha256Digest } from "./skill-sources";

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
    expect(client.getInstructions()).toContain("load_super_tighten");
  });

  it("exposes the complete skill through skills/list and skills/get", async () => {
    const listResult = await client.request(
      { method: "skills/list", params: {} },
      skillsListResultSchema,
    );
    expect(listResult).toEqual(getSkillCatalog());
    expect(listResult.skills.map((entry) => entry.frontmatter.name)).toEqual(["nuko-nova-unslop", "super-tighten"]);
    for (const entry of listResult.skills) {
      const getResult = await client.request(
        { method: "skills/get", params: { uri: entry.uri } },
        skillGetResultSchema,
      );

      expect(getResult.skill).toEqual(entry);
    }
  });

  it.each([
    "skill://nuko-nova-unslop/unknown/SKILL.md",
    "skill://nuko-nova-unslop/super-tighten/references/tighten.md",
    "skill://nuko-nova-unslop/nuko-nova-unslop/references/tighten.md",
    "skill://nuko-nova-unslop/super-tighten/SKILL.md/extra",
  ])("rejects a non-primary skill URI: %s", async (uri) => {
    await expect(client.request(
      { method: "skills/get", params: { uri } },
      skillGetResultSchema,
    )).rejects.toMatchObject({ code: -32602 });
  });

  it("rejects an unrecognized skill page and extra get parameters", async () => {
    await expect(client.request(
      { method: "skills/list", params: { cursor: "next" } },
      skillsListResultSchema,
    )).rejects.toMatchObject({ code: -32602 });
    await expect(client.request(
      { method: "skills/get", params: { uri: getSuperTightenSkill().uri, prose: "Rewrite me" } },
      skillGetResultSchema,
    )).rejects.toMatchObject({ code: -32602 });
  });

  it("returns every declared skill resource with matching text", async () => {
    const listResult = await client.request(
      { method: "skills/list", params: {} },
      skillsListResultSchema,
    );
    const declaredResources = listResult.skills.flatMap((entry) => entry.resources);
    const { resources: advertisedResources } = await client.listResources();
    expect(advertisedResources.map(({ uri }) => uri).sort()).toEqual(declaredResources.map(({ uri }) => uri).sort());
    expect(new Set(advertisedResources.map(({ name }) => name)).size).toBe(advertisedResources.length);

    for (const resource of declaredResources) {
      const expected = listAllSkillResources().find(({ uri }) => uri === resource.uri)!;
      const result = await client.readResource({ uri: resource.uri });
      expect(result.contents).toHaveLength(1);
      expect(result.contents[0]).toMatchObject({ uri: resource.uri, text: expected.content });
      const content = result.contents[0]!;
      expect("text" in content).toBe(true);
      if (!("text" in content)) throw new Error("Expected a text skill resource");
      expect(await sha256Digest(content.text)).toBe(resource.digest);
      if (resource.uri.endsWith(".md")) {
        expect(content.mimeType).toBe("text/markdown");
      }
    }
  });

  it("does not resolve cross-package or arbitrary resource paths", async () => {
    await expect(client.readResource({ uri: "skill://nuko-nova-unslop/super-tighten/references/tighten.md" })).rejects.toBeDefined();
    await expect(client.readResource({ uri: "file:///etc/passwd" })).rejects.toBeDefined();
  });

  it("offers only package-loading tools and accepts no writing input", async () => {
    const { tools } = await client.listTools();

    expect(tools.map((tool) => tool.name)).toEqual([
      "load_nuko_nova_unslop",
      "load_super_tighten",
      "read_nuko_nova_reference",
    ]);
    for (const tool of tools) {
      expect(tool.annotations).toMatchObject({
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      });
      if (tool.name.startsWith("load_")) {
        expect(tool.inputSchema).toMatchObject({
          type: "object",
          properties: {},
          additionalProperties: false,
        });
      }
    }
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
    expect(loaded.content).toEqual([{ type: "text", text: getPrimarySkill().content }]);

    const reference = await client.callTool({
      name: "read_nuko_nova_reference",
      arguments: { name: "tighten.md" },
    });
    expect(reference.isError).not.toBe(true);
    expect(reference.content).toEqual([{ type: "text", text: getReference("tighten.md").content }]);

    const rejected = await client.callTool({
      name: "read_nuko_nova_reference",
      arguments: { name: "../../AGENTS.md" },
    });

    expect(rejected.isError).toBe(true);
  });

  it.each([{}, undefined])("loads the entire standalone skill in one response with arguments %j", async (arguments_) => {
    const skill = getSuperTightenSkill();
    const loaded = await client.callTool({ name: "load_super_tighten", arguments: arguments_ });

    expect(loaded.isError).not.toBe(true);
    expect(loaded.content).toEqual([{ type: "text", text: skill.content }]);
    expect(loaded.structuredContent).toEqual({
      name: skill.name,
      version: skill.version,
      commitSha: skill.commitSha,
      uri: skill.uri,
      digest: skill.digest,
      instructions: skill.content,
      references: [],
    });
  });

  it.each(["load_nuko_nova_unslop", "load_super_tighten"])("rejects prose and any extra argument on %s", async (name) => {
    for (const arguments_ of [{ prose: "Rewrite this" }, { name: "tighten.md" }, { skill: "nuko-nova-unslop" }]) {
      const result = await client.callTool({ name, arguments: arguments_ });
      expect(result.isError).toBe(true);
      expect(result.structuredContent).toBeUndefined();
    }
  });
});
