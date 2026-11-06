import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { buildSkillPackages, renderSkillPackageModule } from "./build-skill-packages.mjs";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "../../..");
const outputPath = path.join(repositoryRoot, "apps/mcp/src/skill-package.generated.ts");

const packages = await buildSkillPackages(repositoryRoot);

await mkdir(path.dirname(outputPath), { recursive: true });
await writeFile(outputPath, renderSkillPackageModule(packages), "utf8");
