import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

export const MAX_FILES = 100;
export const MAX_PRIMARY_BYTES = 256 * 1024;
export const MAX_SUPPORTING_BYTES = 1024 * 1024;
export const MAX_TOTAL_BYTES = 5 * 1024 * 1024;

const PRIMARY_SKILL_PATH = "SKILL.md";

// The only list of served skills. The MCP server registers one load tool and one
// resource set per entry, and reads references from the entry marked primary.
export const SERVED_SKILLS = Object.freeze([
  {
    name: "nuko-nova-unslop",
    primary: true,
    loadTool: {
      name: "load_nuko_nova_unslop",
      title: "Load Unslop",
      description:
        "Load the complete Nuko Nova Unslop writing standard. Use it when the user invokes @Unslop or asks for human, direct, no-slop, no-cringe writing.",
    },
  },
  {
    name: "super-tighten",
    primary: false,
    loadTool: {
      name: "load_super_tighten",
      title: "Load Super Tighten",
      description:
        "Load the complete standalone Super Tighten skill to combine human writing, useful compression, and ASD-STE100 Simplified Technical English rules while preserving facts and meaning. Use it when the user invokes super-tighten, Super Tighten, or requests all three together. No other skill or reference needs to be loaded.",
    },
  },
]);

async function collectFiles(directory, uriRoot, relativeDirectory = "") {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];

  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    if (entry.name === "__pycache__" || entry.name.endsWith(".pyc")) {
      continue;
    }

    const relativePath = path.posix.join(relativeDirectory, entry.name);
    const absolutePath = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      files.push(...(await collectFiles(absolutePath, uriRoot, relativePath)));
    } else if (entry.isFile()) {
      const content = await readFile(absolutePath, "utf8");
      const digest = createHash("sha256").update(content, "utf8").digest("hex");
      files.push({
        path: relativePath,
        uri: `${uriRoot}/${relativePath}`,
        digest: `sha256:${digest}`,
        content,
      });
    }
  }

  return files;
}

function readCommitSha(rootDirectory) {
  if (process.env.GITHUB_SHA) {
    return process.env.GITHUB_SHA;
  }

  try {
    return execFileSync("git", ["rev-parse", "HEAD"], {
      cwd: rootDirectory,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return "unknown";
  }
}

export function validateServedSkills(skills) {
  const primaryCount = skills.filter((skill) => skill.primary === true).length;
  if (primaryCount !== 1) {
    throw new Error(`Exactly one served skill must be primary; found ${primaryCount}`);
  }

  for (const field of ["name", "loadTool.name"]) {
    const seen = new Set();
    for (const skill of skills) {
      const value = field === "name" ? skill.name : skill.loadTool.name;
      if (seen.has(value)) {
        throw new Error(`Served skills repeat ${field}: ${value}`);
      }
      seen.add(value);
    }
  }
}

export function validateImportLimits(resources) {
  if (resources.length > MAX_FILES) {
    throw new Error(`Skill package has ${resources.length} files; the limit is ${MAX_FILES}`);
  }

  const normalizedPaths = new Set();
  let totalBytes = 0;

  for (const resource of resources) {
    const normalizedPath = resource.path.normalize("NFC");
    if (normalizedPaths.has(normalizedPath)) {
      throw new Error(`Skill package has a normalized path conflict: ${resource.path}`);
    }
    normalizedPaths.add(normalizedPath);

    const bytes = Buffer.byteLength(resource.content, "utf8");
    const limit = resource.path === PRIMARY_SKILL_PATH ? MAX_PRIMARY_BYTES : MAX_SUPPORTING_BYTES;
    if (bytes > limit) {
      throw new Error(`Skill package file exceeds its import limit: ${resource.path}`);
    }
    totalBytes += bytes;
  }

  if (totalBytes > MAX_TOTAL_BYTES) {
    throw new Error(`Skill package is ${totalBytes} bytes; the limit is ${MAX_TOTAL_BYTES}`);
  }
}

export async function buildSkillPackages(
  rootDirectory,
  { skills = SERVED_SKILLS, commitSha = readCommitSha(rootDirectory) } = {},
) {
  validateServedSkills(skills);

  const manifest = JSON.parse(
    await readFile(path.join(rootDirectory, ".codex-plugin/plugin.json"), "utf8"),
  );
  const packages = [];

  for (const skill of skills) {
    const uriRoot = `skill://${manifest.name}/${skill.name}`;
    const resources = await collectFiles(path.join(rootDirectory, "skills", skill.name), uriRoot);
    validateImportLimits(resources);
    if (!resources.some((resource) => resource.path === PRIMARY_SKILL_PATH)) {
      throw new Error(`Skill package is missing SKILL.md: ${skill.name}`);
    }
    packages.push({
      name: skill.name,
      primary: skill.primary,
      loadTool: { ...skill.loadTool },
      version: manifest.version,
      commitSha,
      uriRoot,
      resources,
    });
  }

  return packages;
}

export function renderSkillPackageModule(packages) {
  return `// Generated by scripts/generate-skill-package.mjs. Do not edit.\n` +
    `export const GENERATED_SKILL_PACKAGES = ${JSON.stringify(packages, null, 2)} as const;\n`;
}
