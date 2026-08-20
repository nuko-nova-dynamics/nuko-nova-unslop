import { describe, expect, it } from "vitest";

import {
  getPrimarySkill,
  getReference,
  getSkillCatalog,
  listSkillResources,
} from "../src/skill-package";

describe("Nuko Nova Unslop skill package", () => {
  it("serves the released skill as the primary resource", () => {
    const skill = getPrimarySkill();

    expect(skill.name).toBe("nuko-nova-unslop");
    expect(skill.version).toMatch(/^0\.5\.1/);
    expect(skill.uri).toBe("skill://nuko-nova-unslop/nuko-nova-unslop/SKILL.md");
    expect(skill.content).toContain("# Nuko Nova Unslop");
    expect(skill.content).toContain("## Always-on human-writing standard");
  });

  it("publishes only files from the skill package", () => {
    const resources = listSkillResources();

    expect(resources.length).toBeGreaterThan(5);
    expect(resources.every((resource) => resource.uri.startsWith("skill://nuko-nova-unslop/nuko-nova-unslop/"))).toBe(true);
    expect(resources.some((resource) => resource.uri.endsWith("references/pattern-catalog.md"))).toBe(true);
    expect(resources.some((resource) => resource.uri.endsWith("scripts/unslop_lint.py"))).toBe(true);
    expect(resources.some((resource) => resource.uri.includes("__pycache__"))).toBe(false);
    expect(resources.some((resource) => resource.uri.endsWith(".pyc"))).toBe(false);
    expect(resources.every((resource) => /^sha256:[a-f0-9]{64}$/.test(resource.digest))).toBe(true);
  });

  it("returns the complete OpenAI skill catalog entry", () => {
    const catalog = getSkillCatalog();

    expect(catalog.skills).toHaveLength(1);
    expect(catalog.skills[0]?.frontmatter.name).toBe("nuko-nova-unslop");
    expect(catalog.skills[0]?.frontmatter.description).toContain("Always-on human-writing standard");
    expect(catalog.skills[0]?.resources).toEqual(listSkillResources().map(({ uri, digest }) => ({ uri, digest })));
  });

  it("reads an allowed reference and rejects arbitrary paths", () => {
    expect(getReference("pattern-catalog.md").content).toContain("# Pattern catalog");
    expect(() => getReference("../../AGENTS.md")).toThrow("Unknown Nuko Nova Unslop reference");
  });
});
