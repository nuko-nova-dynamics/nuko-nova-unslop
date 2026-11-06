import {
  INVALID_PARAMS,
  McpServer,
  ProtocolError,
} from "@modelcontextprotocol/server";
import { z } from "zod";

import {
  findPrimarySkill,
  getSkillCatalog,
  listServedSkills,
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
  const servedSkills = listServedSkills();
  const primary = findPrimarySkill(servedSkills);
  const catalog = getSkillCatalog();

  if (primary.references.length === 0) {
    throw new Error("Nuko Nova Unslop has no supporting references");
  }

  const readReferenceInputSchema = z
    .object({
      name: z
        .enum(primary.references as [string, ...string[]])
        .describe(`A reference filename listed by ${primary.loadTool.name}`),
    })
    .strict();

  const server = new McpServer(
    {
      name: SERVER_NAME,
      title: "Unslop",
      version: primary.version,
    },
    {
      capabilities: {
        extensions: {
          [SKILLS_EXTENSION]: {},
        },
      },
      instructions:
        "When the user invokes Unslop or requests the Nuko Nova Unslop writing standard, call load_nuko_nova_unslop before drafting. Read a named reference only when the loaded skill routes to it. When the user invokes Super Tighten or super-tighten, call load_super_tighten for its complete standalone instructions. This server is read-only and never accepts user prose.",
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
      const catalogEntry = catalog.skills.find((entry) => entry.uri === uri);
      if (!catalogEntry) {
        throw invalidParams(`Unknown skill URI: ${uri}`);
      }

      return { skill: catalogEntry };
    },
  );

  for (const servedSkill of servedSkills) {
    for (const resource of servedSkill.resources) {
      const resourceName = servedSkill.primary
        ? resource.path
        : new URL(resource.uri).pathname.slice(1);
      server.registerResource(
        resourceName,
        resource.uri,
        {
          title: resourceName,
          description: servedSkill.primary
            ? `Nuko Nova Unslop package file: ${resource.path}`
            : `Standalone skill package file: ${resourceName}`,
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
  }

  for (const servedSkill of servedSkills) {
    server.registerTool(
      servedSkill.loadTool.name,
      {
        title: servedSkill.loadTool.title,
        description: servedSkill.loadTool.description,
        inputSchema: z.object({}).strict(),
        outputSchema: loadSkillOutputSchema,
        annotations: readOnlyAnnotations,
      },
      async () => ({
        content: toolText(servedSkill.content),
        structuredContent: servedSkill.loadOutput,
      }),
    );
  }

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
        reference = primary.readReference(name);
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
