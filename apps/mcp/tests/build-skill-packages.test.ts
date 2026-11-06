import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  buildSkillPackages,
  MAX_FILES,
  MAX_PRIMARY_BYTES,
  MAX_SUPPORTING_BYTES,
  MAX_TOTAL_BYTES,
  renderSkillPackageModule,
  type ServedSkillConfig,
  validateImportLimits,
} from "../scripts/build-skill-packages.mjs";
import { sha256Digest } from "./skill-sources";

const SKILL_MD = "---\nname: demo\ndescription: Demo skill.\n---\n\n# Demo\n";

function servedSkill(name: string, primary: boolean, toolName = `load_${name}`): ServedSkillConfig {
  return { name, primary, loadTool: { name: toolName, title: name, description: `Load ${name}.` } };
}

const DEMO_SKILLS = [servedSkill("demo", true)];

describe("skill package builder", () => {
  let root: string;

  async function writeFixture(relativePath: string, content: string) {
    const target = join(root, relativePath);
    await mkdir(dirname(target), { recursive: true });
    await writeFile(target, content);
  }

  function build(skills: readonly ServedSkillConfig[] = DEMO_SKILLS) {
    return buildSkillPackages(root, { skills, commitSha: "fixture-sha" });
  }

  beforeEach(async () => {
    root = await mkdtemp(join(tmpdir(), "unslop-skill-package-"));
    await writeFixture(
      ".codex-plugin/plugin.json",
      JSON.stringify({ name: "fixture-plugin", version: "1.2.3" }),
    );
  });

  afterEach(async () => {
    await rm(root, { recursive: true, force: true });
  });

  it("builds sorted, hashed resources and carries the served-skill fields", async () => {
    await writeFixture("skills/demo/SKILL.md", SKILL_MD);
    await writeFixture("skills/demo/references/b.md", "B\n");
    await writeFixture("skills/demo/references/a.md", "A\n");
    await writeFixture("skills/demo/scripts/__pycache__/lint.cpython-313.pyc", "x");
    await writeFixture("skills/demo/scripts/lint.pyc", "x");

    const packages = await build();

    expect(packages).toHaveLength(1);
    const [built] = packages;
    expect(built).toMatchObject({
      ...DEMO_SKILLS[0],
      version: "1.2.3",
      commitSha: "fixture-sha",
      uriRoot: "skill://fixture-plugin/demo",
    });
    expect(built!.resources.map(({ path }) => path)).toEqual([
      "references/a.md",
      "references/b.md",
      "SKILL.md",
    ]);
    for (const resource of built!.resources) {
      expect(resource.uri).toBe(`skill://fixture-plugin/demo/${resource.path}`);
      expect(resource.digest).toBe(await sha256Digest(resource.content));
    }
    expect(renderSkillPackageModule(packages)).toContain(
      `export const GENERATED_SKILL_PACKAGES = ${JSON.stringify(packages, null, 2)} as const;`,
    );
  });

  it("accepts files exactly at each size limit", async () => {
    await writeFixture("skills/demo/SKILL.md", "x".repeat(MAX_PRIMARY_BYTES));
    await writeFixture("skills/demo/references/large.md", "x".repeat(MAX_SUPPORTING_BYTES));

    await expect(build()).resolves.toHaveLength(1);
  });

  it("rejects a package with more files than the limit", async () => {
    await writeFixture("skills/demo/SKILL.md", SKILL_MD);
    for (let index = 0; index < MAX_FILES; index += 1) {
      await writeFixture(`skills/demo/references/${String(index).padStart(3, "0")}.md`, "x");
    }

    await expect(build()).rejects.toThrow(`the limit is ${MAX_FILES}`);
  });

  it("rejects a SKILL.md over the primary file limit", async () => {
    await writeFixture("skills/demo/SKILL.md", "x".repeat(MAX_PRIMARY_BYTES + 1));

    await expect(build()).rejects.toThrow("exceeds its import limit: SKILL.md");
  });

  it("rejects a supporting file over the supporting file limit", async () => {
    await writeFixture("skills/demo/SKILL.md", SKILL_MD);
    await writeFixture("skills/demo/references/large.md", "x".repeat(MAX_SUPPORTING_BYTES + 1));

    await expect(build()).rejects.toThrow("exceeds its import limit: references/large.md");
  });

  it("rejects a package over the total size limit", async () => {
    await writeFixture("skills/demo/SKILL.md", SKILL_MD);
    const fileCount = Math.ceil(MAX_TOTAL_BYTES / MAX_SUPPORTING_BYTES);
    for (let index = 0; index < fileCount; index += 1) {
      await writeFixture(`skills/demo/references/${index}.md`, "x".repeat(MAX_SUPPORTING_BYTES));
    }

    await expect(build()).rejects.toThrow(`the limit is ${MAX_TOTAL_BYTES}`);
  });

  it("rejects a package without SKILL.md", async () => {
    await writeFixture("skills/demo/references/a.md", "A\n");

    await expect(build()).rejects.toThrow("missing SKILL.md: demo");
  });

  // APFS and other normalization-insensitive file systems store both spellings
  // as one file, so this case runs on in-memory resources instead of a fixture.
  it("rejects paths that conflict after NFC normalization", () => {
    expect(() =>
      validateImportLimits([
        { path: "references/café.md", content: "A" },
        { path: "references/café.md", content: "B" },
      ]),
    ).toThrow("normalized path conflict");
  });

  it.each([
    ["no primary skill", [servedSkill("demo", false)], "found 0"],
    ["two primary skills", [servedSkill("demo", true), servedSkill("other", true)], "found 2"],
    ["a repeated skill name", [servedSkill("demo", true), servedSkill("demo", false, "load_other")], "repeat name: demo"],
    ["a repeated load tool", [servedSkill("demo", true), servedSkill("other", false, "load_demo")], "repeat loadTool.name: load_demo"],
  ])("rejects served skills with %s", async (_label, skills, message) => {
    await writeFixture("skills/demo/SKILL.md", SKILL_MD);
    await writeFixture("skills/other/SKILL.md", SKILL_MD);

    await expect(build(skills)).rejects.toThrow(message);
  });
});
