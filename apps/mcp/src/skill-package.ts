import { GENERATED_SKILL_PACKAGE } from "./skill-package.generated";

const PRIMARY_SKILL_PATH = "SKILL.md";
const REFERENCE_PREFIX = "references/";

export type SkillResource = {
  path: string;
  uri: string;
  digest: `sha256:${string}`;
  content: string;
};

function findResourceByPath(resourcePath: string): SkillResource {
  const resource = GENERATED_SKILL_PACKAGE.resources.find(
    (candidate) => candidate.path === resourcePath,
  );

  if (!resource) {
    throw new Error(`Unknown Nuko Nova Unslop resource: ${resourcePath}`);
  }

  return resource;
}

function parseFrontmatter(content: string) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n/);
  if (!match) {
    throw new Error("Nuko Nova Unslop SKILL.md is missing YAML frontmatter");
  }

  const frontmatter = match[1];
  const name = frontmatter.match(/^name:\s*(.+)$/m)?.[1]?.trim();
  const description = frontmatter.match(/^description:\s*(.+)$/m)?.[1]?.trim();

  if (!name || !description) {
    throw new Error("Nuko Nova Unslop SKILL.md must declare name and description");
  }

  return { name, description };
}

export function listSkillResources(): SkillResource[] {
  return GENERATED_SKILL_PACKAGE.resources.map((resource) => ({ ...resource }));
}

export function getPrimarySkill() {
  const resource = findResourceByPath(PRIMARY_SKILL_PATH);
  const frontmatter = parseFrontmatter(resource.content);

  return {
    ...frontmatter,
    version: GENERATED_SKILL_PACKAGE.version,
    commitSha: GENERATED_SKILL_PACKAGE.commitSha,
    uri: resource.uri,
    digest: resource.digest,
    content: resource.content,
    references: GENERATED_SKILL_PACKAGE.resources
      .filter((candidate) => candidate.path.startsWith(REFERENCE_PREFIX))
      .map((candidate) => candidate.path.slice(REFERENCE_PREFIX.length)),
  };
}

export function getReference(referenceName: string) {
  if (
    referenceName.includes("/") ||
    referenceName.includes("\\") ||
    !referenceName.endsWith(".md")
  ) {
    throw new Error(`Unknown Nuko Nova Unslop reference: ${referenceName}`);
  }

  const resourcePath = `${REFERENCE_PREFIX}${referenceName}`;
  const resource = GENERATED_SKILL_PACKAGE.resources.find(
    (candidate) => candidate.path === resourcePath,
  );

  if (!resource) {
    throw new Error(`Unknown Nuko Nova Unslop reference: ${referenceName}`);
  }

  return { ...resource };
}

export function getSkillCatalog() {
  const skill = getPrimarySkill();

  return {
    skills: [
      {
        uri: skill.uri,
        frontmatter: {
          name: skill.name,
          description: skill.description,
        },
        resources: listSkillResources().map(({ uri, digest }) => ({ uri, digest })),
      },
    ],
  };
}
