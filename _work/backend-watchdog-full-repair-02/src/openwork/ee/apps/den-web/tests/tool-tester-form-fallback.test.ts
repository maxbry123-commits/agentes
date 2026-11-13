import { describe, expect, test } from "bun:test";
import {
  schemaSupportsForm,
  serializeFormValues,
} from "../app/(den)/dashboard/_components/tool-tester/schema-form";

describe("Tool Tester schema form fallback", () => {
  test("supports flat primitive and enum object properties", () => {
    expect(schemaSupportsForm({
      type: "object",
      properties: {
        title: { type: "string" },
        count: { type: "number" },
        state: { enum: ["open", "closed"] },
      },
    })).toBe(true);
  });

  test("rejects nested object properties", () => {
    expect(schemaSupportsForm({
      type: "object",
      properties: { filter: { type: "object", properties: { name: { type: "string" } } } },
    })).toBe(false);
  });

  test("rejects array properties", () => {
    expect(schemaSupportsForm({
      type: "object",
      properties: { tags: { type: "array", items: { type: "string" } } },
    })).toBe(false);
  });

  test("rejects empty or missing properties", () => {
    expect(schemaSupportsForm({ type: "object", properties: {} })).toBe(false);
    expect(schemaSupportsForm({ type: "object" })).toBe(false);
  });

  test("rejects non-object schemas", () => {
    expect(schemaSupportsForm({ type: "string", properties: { value: { type: "string" } } })).toBe(false);
  });

  test("omits empty optional strings and coerces numbers", () => {
    expect(serializeFormValues({
      type: "object",
      properties: {
        note: { type: "string" },
        count: { type: "number" },
      },
      required: ["count"],
    }, {
      note: "",
      count: "12.5",
    })).toEqual({ count: 12.5 });
  });
});
