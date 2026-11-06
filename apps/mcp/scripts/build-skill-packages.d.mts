export type ServedSkillConfig = {
  name: string;
  primary: boolean;
  loadTool: { name: string; title: string; description: string };
};

export type BuiltSkillResource = {
  path: string;
  uri: string;
  digest: `sha256:${string}`;
  content: string;
};

export type BuiltSkillPackage = ServedSkillConfig & {
  version: string;
  commitSha: string;
  uriRoot: string;
  resources: BuiltSkillResource[];
};

export declare const MAX_FILES: number;
export declare const MAX_PRIMARY_BYTES: number;
export declare const MAX_SUPPORTING_BYTES: number;
export declare const MAX_TOTAL_BYTES: number;
export declare const SERVED_SKILLS: readonly ServedSkillConfig[];

export declare function validateServedSkills(skills: readonly ServedSkillConfig[]): void;
export declare function validateImportLimits(
  resources: readonly { path: string; content: string }[],
): void;
export declare function buildSkillPackages(
  rootDirectory: string,
  options?: { skills?: readonly ServedSkillConfig[]; commitSha?: string },
): Promise<BuiltSkillPackage[]>;
export declare function renderSkillPackageModule(packages: readonly BuiltSkillPackage[]): string;
