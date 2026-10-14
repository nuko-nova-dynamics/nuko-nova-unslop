import { describe, expect, it } from "vitest";
import { primarySkillSource, superTightenSource, patternCatalogSource, sha256Digest } from "./skill-sources";

import {
  getPrimarySkill,
  getReference,
  getSkillCatalog,
  getSuperTightenSkill,
  listAllSkillResources,
  listSkillResources,
} from "../src/skill-package";

const utf8Bytes = (content: string) => new TextEncoder().encode(content).byteLength;

describe("Nuko Nova Unslop skill package", () => {
  it("serves the released skill as the primary resource", () => {
    const skill = getPrimarySkill();

    expect(skill.name).toBe("nuko-nova-unslop");
    expect(skill.version).toBe("0.9.0");
    expect(skill.uri).toBe("skill://nuko-nova-unslop/nuko-nova-unslop/SKILL.md");
    expect(skill.content).toBe(primarySkillSource);
  });

  it("publishes only files from the skill package", () => {
    const resources = listSkillResources();

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

  it("returns the complete OpenAI skill catalog entry", () => {
    const catalog = getSkillCatalog();

    expect(catalog.skills).toHaveLength(2);
    expect(catalog.skills[0]?.frontmatter.name).toBe("nuko-nova-unslop");
    expect(catalog.skills[0]?.frontmatter.description).toBe(getPrimarySkill().description);
    expect(catalog.skills[0]?.resources).toEqual(listSkillResources().map(({ uri, digest }) => ({ uri, digest })));
    const standalone = getSuperTightenSkill();
    expect(catalog.skills[1]).toEqual({
      uri: standalone.uri,
      frontmatter: { name: standalone.name, description: standalone.description },
      resources: listAllSkillResources()
        .filter(({ uri }) => uri.startsWith("skill://nuko-nova-unslop/super-tighten/"))
        .map(({ uri, digest }) => ({ uri, digest })),
    });
    const declaredUris = catalog.skills.flatMap((entry) => entry.resources.map(({ uri }) => uri));
    expect(new Set(declaredUris).size).toBe(declaredUris.length);
    expect(declaredUris).toEqual(listAllSkillResources().map(({ uri }) => uri));
    for (const entry of catalog.skills) {
      const root = entry.uri.slice(0, -"SKILL.md".length);
      expect(entry.resources.every(({ uri }) => uri.startsWith(root))).toBe(true);
    }
  });

  it("packages the standalone skill verbatim without reference dependencies", async () => {
    const skill = getSuperTightenSkill();

    expect(skill.name).toBe("super-tighten");
    expect(skill.version).toBe(getPrimarySkill().version);
    expect(skill.uri).toBe("skill://nuko-nova-unslop/super-tighten/SKILL.md");
    expect(skill.content).toBe(superTightenSource);
    expect(skill.references).toEqual([]);
    expect(skill.digest).toBe(await sha256Digest(superTightenSource));
  });

  it("hashes every shipped resource from its actual contents", async () => {
    for (const resource of listAllSkillResources()) {
      expect(resource.digest).toBe(await sha256Digest(resource.content));
    }
  });

  it.each(["nuko-nova-unslop", "super-tighten"])("keeps %s inside OpenAI's skill import limits", (name) => {
    const resources = listAllSkillResources().filter(({ uri }) => uri.startsWith(`skill://nuko-nova-unslop/${name}/`));
    const totalBytes = resources.reduce(
      (total, resource) => total + utf8Bytes(resource.content),
      0,
    );
    const normalizedPaths = resources.map((resource) => resource.path.normalize("NFC"));

    expect(resources.length).toBeLessThanOrEqual(100);
    expect(new Set(normalizedPaths).size).toBe(normalizedPaths.length);
    expect(
      utf8Bytes(resources.find((resource) => resource.path === "SKILL.md")!.content),
    ).toBeLessThanOrEqual(256 * 1024);
    expect(
      resources
        .filter((resource) => resource.path !== "SKILL.md")
        .every(
          (resource) => utf8Bytes(resource.content) <= 1024 * 1024,
        ),
    ).toBe(true);
    expect(totalBytes).toBeLessThanOrEqual(5 * 1024 * 1024);
  });

  it("reads an allowed reference and rejects arbitrary paths", () => {
    expect(getReference("pattern-catalog.md").content).toBe(patternCatalogSource);
    expect(() => getReference("../../AGENTS.md")).toThrow("Unknown Nuko Nova Unslop reference");
  });
});
