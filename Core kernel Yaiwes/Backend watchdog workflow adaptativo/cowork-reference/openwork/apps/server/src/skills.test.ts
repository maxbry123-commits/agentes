import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { deleteSkill, listSkills, renderSkillContentForResponse } from "./skills.js";
import { exists } from "./utils.js";

let workspace: string;

async function writeSkill(dir: string, name: string) {
  await mkdir(dir, { recursive: true });
  await writeFile(join(dir, "SKILL.md"), `---\nname: ${name}\ndescription: Test skill ${name}\n---\n\nBody\n`, "utf8");
}

beforeEach(async () => {
  workspace = await mkdtemp(join(tmpdir(), "openwork-skills-"));
  await mkdir(join(workspace, ".git"), { recursive: true });
});

afterEach(async () => {
  await rm(workspace, { recursive: true, force: true });
});

describe("deleteSkill", () => {
  test("deletes a flat skill", async () => {
    const dir = join(workspace, ".opencode", "skills", "flat-skill");
    await writeSkill(dir, "flat-skill");
    await deleteSkill(workspace, "flat-skill");
    expect(await exists(dir)).toBe(false);
  });

  test("deletes a plugin-namespaced (nested) skill", async () => {
    // Marketplace plugin bundles install skills under skills/<plugin>/<name>/
    const dir = join(workspace, ".opencode", "skills", "bio-research-plugin", "instrument-data-to-allotrope");
    await writeSkill(dir, "instrument-data-to-allotrope");

    const listed = await listSkills(workspace, false);
    expect(listed.map((s) => s.name)).toContain("instrument-data-to-allotrope");

    await deleteSkill(workspace, "instrument-data-to-allotrope");
    expect(await exists(dir)).toBe(false);
  });

  test("404s for unknown skills", async () => {
    await expect(deleteSkill(workspace, "does-not-exist")).rejects.toThrow("Skill not found");
  });
});

describe("listSkills", () => {
  test("returns skills with malformed YAML frontmatter as visible errors", async () => {
    const validDir = join(workspace, ".opencode", "skills", "valid-skill");
    await writeSkill(validDir, "valid-skill");

    const invalidDir = join(workspace, ".opencode", "skills", "invalid-skill");
    await mkdir(invalidDir, { recursive: true });
    const invalidContent = `---\nname: invalid-skill\ndescription: Use when searching the web, looking up facts, researching technology: trends\n---\n\nBody\n`;
    await writeFile(
      join(invalidDir, "SKILL.md"),
      invalidContent,
      "utf8",
    );

    const originalWarn = console.warn;
    const warnings: unknown[][] = [];
    console.warn = (...args: unknown[]) => {
      warnings.push(args);
    };
    try {
      const listed = await listSkills(workspace, false);
      const names = listed.map((skill) => skill.name);
      const invalid = listed.find((skill) => skill.name === "invalid-skill");

      expect(names).toContain("valid-skill");
      expect(names).toContain("invalid-skill");
      expect(invalid?.description.startsWith("ERROR: Invalid skill frontmatter")).toBe(true);
      expect(invalid?.error).toContain("Nested mappings are not allowed");
      expect(invalid ? renderSkillContentForResponse(invalid, invalidContent) : "").toContain("ERROR: This skill has invalid YAML frontmatter");
      expect(invalid ? renderSkillContentForResponse(invalid, invalidContent) : "").toContain(invalidContent);
      expect(warnings).toHaveLength(1);
      expect(warnings[0]?.[0]).toBe("[openwork:skills] Found invalid skill frontmatter");
    } finally {
      console.warn = originalWarn;
    }
  });
});
