import { GENERATED_SKILL_PACKAGES } from "./skill-package.generated";

const PRIMARY_SKILL_PATH = "SKILL.md";
const REFERENCE_PREFIX = "references/";

export type SkillResource = {
  path: string;
  uri: string;
  digest: `sha256:${string}`;
  content: string;
};

export type LoadTool = {
  name: string;
  title: string;
  description: string;
};

export type LoadSkillOutput = {
  name: string;
  version: string;
  commitSha: string;
  uri: string;
  digest: string;
  instructions: string;
  references: string[];
};

export type SkillCatalogEntry = {
  uri: string;
  frontmatter: { name: string; description: string };
  resources: { uri: string; digest: string }[];
};

/** One served skill: its package, its load tool, and its catalog entry. */
export type ServedSkill = {
  /** Frontmatter name. */
  name: string;
  /** Frontmatter description. */
  description: string;
  /** True for the one skill whose references the reference reader serves. */
  primary: boolean;
  version: string;
  commitSha: string;
  /** URI of the skill's SKILL.md. */
  uri: string;
  /** Digest of the skill's SKILL.md. */
  digest: `sha256:${string}`;
  /** Text of the skill's SKILL.md. */
  content: string;
  /** Filenames under references/, without the prefix. */
  references: string[];
  /** Every packaged file, in package order. */
  resources: SkillResource[];
  loadTool: LoadTool;
  /** Structured result of the skill's load tool. */
  loadOutput: LoadSkillOutput;
  /** Entry for skills/list and skills/get. */
  catalogEntry: SkillCatalogEntry;
  /** Returns one file under references/ by filename, or throws. */
  readReference(referenceName: string): SkillResource;
};

type GeneratedSkillPackage = (typeof GENERATED_SKILL_PACKAGES)[number];

function findResource(
  resources: readonly SkillResource[],
  resourcePath: string,
  errorMessage: string,
): SkillResource {
  const resource = resources.find((candidate) => candidate.path === resourcePath);
  if (!resource) {
    throw new Error(errorMessage);
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

function toServedSkill(skillPackage: GeneratedSkillPackage): ServedSkill {
  const resources: SkillResource[] = skillPackage.resources.map((resource) => ({ ...resource }));
  const skillFile = findResource(
    resources,
    PRIMARY_SKILL_PATH,
    `Unknown ${skillPackage.name} resource: ${PRIMARY_SKILL_PATH}`,
  );
  const { name, description } = parseFrontmatter(skillFile.content, skillPackage.name);
  const references = resources
    .filter((candidate) => candidate.path.startsWith(REFERENCE_PREFIX))
    .map((candidate) => candidate.path.slice(REFERENCE_PREFIX.length));

  return {
    name,
    description,
    primary: skillPackage.primary,
    version: skillPackage.version,
    commitSha: skillPackage.commitSha,
    uri: skillFile.uri,
    digest: skillFile.digest,
    content: skillFile.content,
    references,
    resources,
    loadTool: { ...skillPackage.loadTool },
    loadOutput: {
      name,
      version: skillPackage.version,
      commitSha: skillPackage.commitSha,
      uri: skillFile.uri,
      digest: skillFile.digest,
      instructions: skillFile.content,
      references: [...references],
    },
    catalogEntry: {
      uri: skillFile.uri,
      frontmatter: { name, description },
      resources: resources.map(({ uri, digest }) => ({ uri, digest })),
    },
    readReference(referenceName) {
      const errorMessage = `Unknown ${skillPackage.name} reference: ${referenceName}`;
      if (
        referenceName.includes("/") ||
        referenceName.includes("\\") ||
        !referenceName.endsWith(".md")
      ) {
        throw new Error(errorMessage);
      }
      return { ...findResource(resources, `${REFERENCE_PREFIX}${referenceName}`, errorMessage) };
    },
  };
}

/** Every served skill, in generated order. Each call returns fresh objects. */
export function listServedSkills(): ServedSkill[] {
  return GENERATED_SKILL_PACKAGES.map(toServedSkill);
}

export function findPrimarySkill(skills: readonly ServedSkill[]): ServedSkill {
  const primary = skills.filter((skill) => skill.primary);
  if (primary.length !== 1) {
    throw new Error(`Expected exactly one primary served skill; found ${primary.length}`);
  }
  return primary[0];
}

export function getPrimarySkill(): ServedSkill {
  return findPrimarySkill(listServedSkills());
}

export function listAllSkillResources(): SkillResource[] {
  return listServedSkills().flatMap((skill) => skill.resources);
}

export function getSkillCatalog(): { skills: SkillCatalogEntry[] } {
  return { skills: listServedSkills().map((skill) => skill.catalogEntry) };
}
