import { describe, expect, it } from "vitest";
import {
  patternCatalogSource,
  pluginManifestSource,
  primarySkillSource,
  sha256Digest,
  superTightenSource,
} from "./skill-sources";

import {
  getPrimarySkill,
  getSkillCatalog,
  listAllSkillResources,
  listServedSkills,
} from "../src/skill-package";

const manifest = JSON.parse(pluginManifestSource) as { name: string; version: string };

describe("Nuko Nova Unslop skill package", () => {
  it("serves the released skill as the primary resource", () => {
    const skill = getPrimarySkill();

    expect(skill.name).toBe("nuko-nova-unslop");
    expect(skill.primary).toBe(true);
    expect(skill.version).toBe(manifest.version);
    expect(skill.uri).toBe("skill://nuko-nova-unslop/nuko-nova-unslop/SKILL.md");
    expect(skill.content).toBe(primarySkillSource);
  });

  it("marks exactly one served skill as primary", () => {
    const primaryNames = listServedSkills()
      .filter((skill) => skill.primary)
      .map((skill) => skill.name);

    expect(primaryNames).toEqual([getPrimarySkill().name]);
  });

  it("publishes only files from the skill package", () => {
    const { resources } = getPrimarySkill();

    expect(resources.length).toBeGreaterThan(5);
    expect(resources.every((resource) => resource.uri.startsWith("skill://nuko-nova-unslop/nuko-nova-unslop/"))).toBe(true);
    expect(resources.some((resource) => resource.uri.endsWith("references/pattern-catalog.md"))).toBe(true);
    expect(resources.some((resource) => resource.uri.endsWith("references/tighten.md"))).toBe(true);
    expect(resources.some((resource) => resource.uri.endsWith("scripts/unslop_lint.py"))).toBe(true);
    expect(resources.some((resource) => resource.uri.endsWith("scripts/markdown_source.py"))).toBe(true);
    expect(resources.some((resource) => resource.uri.includes("__pycache__"))).toBe(false);
    expect(resources.some((resource) => resource.uri.endsWith(".pyc"))).toBe(false);
    expect(resources.every((resource) => /^sha256:[a-f0-9]{64}$/.test(resource.digest))).toBe(true);
    expect(
      resources.every(
        (resource) =>
          !/\/Users\/[^/\s]+\//.test(resource.content) &&
          !/[A-Za-z]:\\Users\\[^\\\s]+\\/.test(resource.content),
      ),
    ).toBe(true);
  });

  it.each(listServedSkills().map((skill) => [skill.name, skill] as const))(
    "describes %s consistently across catalog and load output",
    (_name, skill) => {
      const root = `skill://${manifest.name}/${skill.name}/`;

      expect(skill.version).toBe(manifest.version);
      expect(skill.uri).toBe(`${root}SKILL.md`);
      expect(skill.resources.every(({ uri }) => uri.startsWith(root))).toBe(true);
      expect(skill.catalogEntry).toEqual({
        uri: skill.uri,
        frontmatter: { name: skill.name, description: skill.description },
        resources: skill.resources.map(({ uri, digest }) => ({ uri, digest })),
      });
      expect(skill.loadOutput).toEqual({
        name: skill.name,
        version: skill.version,
        commitSha: skill.commitSha,
        uri: skill.uri,
        digest: skill.digest,
        instructions: skill.content,
        references: skill.references,
      });
      expect(skill.references).toEqual(
        skill.resources
          .filter(({ path }) => path.startsWith("references/"))
          .map(({ path }) => path.slice("references/".length)),
      );
    },
  );

  it("returns the complete OpenAI skill catalog entry", () => {
    const catalog = getSkillCatalog();

    expect(catalog.skills).toEqual(listServedSkills().map((skill) => skill.catalogEntry));
    const declaredUris = catalog.skills.flatMap((entry) => entry.resources.map(({ uri }) => uri));
    expect(new Set(declaredUris).size).toBe(declaredUris.length);
    expect(declaredUris).toEqual(listAllSkillResources().map(({ uri }) => uri));
  });

  it("packages the standalone skill verbatim without reference dependencies", async () => {
    const skill = listServedSkills().find((candidate) => candidate.name === "super-tighten");

    expect(skill).toBeDefined();
    expect(skill!.primary).toBe(false);
    expect(skill!.uri).toBe("skill://nuko-nova-unslop/super-tighten/SKILL.md");
    expect(skill!.content).toBe(superTightenSource);
    expect(skill!.references).toEqual([]);
    expect(skill!.digest).toBe(await sha256Digest(superTightenSource));
  });

  it("hashes every shipped resource from its actual contents", async () => {
    for (const resource of listAllSkillResources()) {
      expect(resource.digest).toBe(await sha256Digest(resource.content));
    }
  });

  it("reads an allowed reference and rejects arbitrary paths", () => {
    const skill = getPrimarySkill();

    expect(skill.readReference("pattern-catalog.md").content).toBe(patternCatalogSource);
    expect(() => skill.readReference("../../AGENTS.md")).toThrow("Unknown nuko-nova-unslop reference");
    expect(() => skill.readReference("missing.md")).toThrow("Unknown nuko-nova-unslop reference");
  });
});
