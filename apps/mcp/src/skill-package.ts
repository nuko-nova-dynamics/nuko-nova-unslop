import { GENERATED_SKILL_PACKAGE, GENERATED_SKILL_PACKAGES } from "./skill-package.generated";

const PRIMARY_SKILL_PATH = "SKILL.md";
const REFERENCE_PREFIX = "references/";

export type SkillResource = {
  path: string;
  uri: string;
  digest: `sha256:${string}`;
  content: string;
};

type SkillPackage = {
  name: string;
  version: string;
  commitSha: string;
  resources: readonly SkillResource[];
};

function findResourceByPath(skillPackage: SkillPackage, resourcePath: string): SkillResource {
  const resource = skillPackage.resources.find(
    (candidate) => candidate.path === resourcePath,
  );

  if (!resource) {
    throw new Error(`Unknown ${skillPackage.name} resource: ${resourcePath}`);
  }

  return resource;
}

function parseFrontmatter(content: string, skillName: string) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n/);
  if (!match) {
    throw new Error(`${skillName} SKILL.md is missing YAML frontmatter`);
  }

  const frontmatter = match[1];
  const name = frontmatter.match(/^name:\s*(.+)$/m)?.[1]?.trim();
  const description = frontmatter.match(/^description:\s*(.+)$/m)?.[1]?.trim();

  if (!name || !description) {
    throw new Error(`${skillName} SKILL.md must declare name and description`);
  }

  return { name, description };
}

export function listSkillResources(): SkillResource[] {
  return GENERATED_SKILL_PACKAGE.resources.map((resource) => ({ ...resource }));
}

export function listAllSkillResources(): SkillResource[] {
  return GENERATED_SKILL_PACKAGES.flatMap((skillPackage) =>
    skillPackage.resources.map((resource) => ({ ...resource })),
  );
}

function getPackagedSkill(skillPackage: SkillPackage) {
  const resource = findResourceByPath(skillPackage, PRIMARY_SKILL_PATH);
  const frontmatter = parseFrontmatter(resource.content, skillPackage.name);

  return {
    ...frontmatter,
    version: skillPackage.version,
    commitSha: skillPackage.commitSha,
    uri: resource.uri,
    digest: resource.digest,
    content: resource.content,
    references: skillPackage.resources
      .filter((candidate) => candidate.path.startsWith(REFERENCE_PREFIX))
      .map((candidate) => candidate.path.slice(REFERENCE_PREFIX.length)),
  };
}

export function getPrimarySkill() {
  return getPackagedSkill(GENERATED_SKILL_PACKAGE);
}

export function getSuperTightenSkill() {
  const skillPackage = GENERATED_SKILL_PACKAGES.find(
    (candidate) => candidate.name === "super-tighten",
  );
  if (!skillPackage) {
    throw new Error("Super Tighten skill package is missing");
  }
  return getPackagedSkill(skillPackage);
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
  return {
    skills: GENERATED_SKILL_PACKAGES.map((skillPackage) => {
      const skill = getPackagedSkill(skillPackage);
      return {
        uri: skill.uri,
        frontmatter: {
          name: skill.name,
          description: skill.description,
        },
        resources: skillPackage.resources.map(({ uri, digest }) => ({ uri, digest })),
      };
    }),
  };
}
