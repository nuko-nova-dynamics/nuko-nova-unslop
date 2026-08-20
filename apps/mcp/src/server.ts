import {
  INVALID_PARAMS,
  McpServer,
  ProtocolError,
} from "@modelcontextprotocol/server";
import { z } from "zod";

import {
  getPrimarySkill,
  getReference,
  getSkillCatalog,
  listSkillResources,
} from "./skill-package";

const SERVER_NAME = "nuko-nova-unslop";
const SKILLS_EXTENSION = "io.modelcontextprotocol/skills";

const skillResourceSchema = z.object({
  uri: z.string(),
  digest: z.string(),
});

const skillEntrySchema = z.object({
  uri: z.string(),
  frontmatter: z.record(z.string(), z.string()),
  resources: z.array(skillResourceSchema),
});

const skillsListParamsSchema = z
  .object({
    cursor: z.string().optional(),
  })
  .strict();

const skillsListResultSchema = z.object({
  skills: z.array(skillEntrySchema),
  nextCursor: z.string().optional(),
});

const skillGetParamsSchema = z
  .object({
    uri: z.string(),
  })
  .strict();

const skillGetResultSchema = z.object({
  skill: skillEntrySchema,
});

const loadSkillOutputSchema = z.object({
  name: z.string(),
  version: z.string(),
  commitSha: z.string(),
  uri: z.string(),
  digest: z.string(),
  instructions: z.string(),
  references: z.array(z.string()),
});

const readReferenceOutputSchema = z.object({
  name: z.string(),
  uri: z.string(),
  digest: z.string(),
  content: z.string(),
});

const readOnlyAnnotations = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
} as const;

function invalidParams(message: string): ProtocolError {
  return new ProtocolError(INVALID_PARAMS, message);
}

function resourceMimeType(resourcePath: string): string {
  if (resourcePath.endsWith(".md")) return "text/markdown";
  if (resourcePath.endsWith(".yaml") || resourcePath.endsWith(".yml")) {
    return "application/yaml";
  }
  if (resourcePath.endsWith(".py")) return "text/x-python";
  return "text/plain";
}

function toolText(content: string) {
  return [{ type: "text" as const, text: content }];
}

export function createNukoNovaUnslopServer(): McpServer {
  const skill = getPrimarySkill();
  const catalog = getSkillCatalog();
  const catalogEntry = catalog.skills[0];

  if (!catalogEntry) {
    throw new Error("Nuko Nova Unslop skill catalog is empty");
  }

  if (skill.references.length === 0) {
    throw new Error("Nuko Nova Unslop has no supporting references");
  }

  const readReferenceInputSchema = z
    .object({
      name: z
        .enum(skill.references as [string, ...string[]])
        .describe("A reference filename listed by load_nuko_nova_unslop"),
    })
    .strict();

  const server = new McpServer(
    {
      name: SERVER_NAME,
      title: "Nuko Nova Unslop",
      version: skill.version,
    },
    {
      capabilities: {
        extensions: {
          [SKILLS_EXTENSION]: {},
        },
      },
      instructions:
        "When the user invokes Nuko Nova Unslop or requests its writing standard, call load_nuko_nova_unslop before drafting. Read a named reference only when the loaded skill routes to it. This server is read-only and never accepts user prose.",
    },
  );

  server.server.setRequestHandler(
    "skills/list",
    { params: skillsListParamsSchema, result: skillsListResultSchema },
    async ({ cursor }) => {
      if (cursor !== undefined) {
        throw invalidParams("Nuko Nova Unslop has no additional skill pages");
      }

      return catalog;
    },
  );

  server.server.setRequestHandler(
    "skills/get",
    { params: skillGetParamsSchema, result: skillGetResultSchema },
    async ({ uri }) => {
      if (uri !== catalogEntry.uri) {
        throw invalidParams(`Unknown skill URI: ${uri}`);
      }

      return { skill: catalogEntry };
    },
  );

  for (const resource of listSkillResources()) {
    server.registerResource(
      resource.path,
      resource.uri,
      {
        title: resource.path,
        description: `Nuko Nova Unslop package file: ${resource.path}`,
        mimeType: resourceMimeType(resource.path),
      },
      async () => ({
        contents: [
          {
            uri: resource.uri,
            mimeType: resourceMimeType(resource.path),
            text: resource.content,
          },
        ],
      }),
    );
  }

  server.registerTool(
    "load_nuko_nova_unslop",
    {
      title: "Load Nuko Nova Unslop",
      description:
        "Load the complete Nuko Nova Unslop writing standard. Use it when the user invokes @Nuko Nova Unslop or asks for human, direct, no-slop, no-cringe writing.",
      inputSchema: z.object({}).strict(),
      outputSchema: loadSkillOutputSchema,
      annotations: readOnlyAnnotations,
    },
    async () => {
      const output = {
        name: skill.name,
        version: skill.version,
        commitSha: skill.commitSha,
        uri: skill.uri,
        digest: skill.digest,
        instructions: skill.content,
        references: skill.references,
      };

      return {
        content: toolText(skill.content),
        structuredContent: output,
      };
    },
  );

  server.registerTool(
    "read_nuko_nova_reference",
    {
      title: "Read a Nuko Nova Unslop reference",
      description:
        "Read one supporting Nuko Nova Unslop reference named by the loaded skill. This tool does not accept prose to rewrite.",
      inputSchema: readReferenceInputSchema,
      outputSchema: readReferenceOutputSchema,
      annotations: readOnlyAnnotations,
    },
    async ({ name }) => {
      let reference;
      try {
        reference = getReference(name);
      } catch {
        throw invalidParams(`Unknown Nuko Nova Unslop reference: ${name}`);
      }

      const output = {
        name,
        uri: reference.uri,
        digest: reference.digest,
        content: reference.content,
      };

      return {
        content: toolText(reference.content),
        structuredContent: output,
      };
    },
  );

  return server;
}
