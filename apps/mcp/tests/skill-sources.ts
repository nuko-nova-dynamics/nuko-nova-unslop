export { default as primarySkillSource } from "../../../skills/nuko-nova-unslop/SKILL.md?raw";
export { default as superTightenSource } from "../../../skills/super-tighten/SKILL.md?raw";
export { default as patternCatalogSource } from "../../../skills/nuko-nova-unslop/references/pattern-catalog.md?raw";

export async function sha256Digest(content: string) {
  const bytes = new TextEncoder().encode(content);
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return `sha256:${Array.from(digest, (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}
