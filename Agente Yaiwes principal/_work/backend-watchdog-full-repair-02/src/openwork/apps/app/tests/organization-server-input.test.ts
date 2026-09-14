import { describe, expect, test } from "bun:test";

import { normalizeOrganizationServerInput } from "../src/app/lib/organization-server-input";

describe("normalizeOrganizationServerInput", () => {
  test("normalizes full URLs and bare hostnames to their origin", () => {
    expect(normalizeOrganizationServerInput("https://openwork.acme.com/werpiweur")).toBe(
      "https://openwork.acme.com",
    );
    expect(normalizeOrganizationServerInput("  openwork.acme.com  ")).toBe(
      "https://openwork.acme.com",
    );
    expect(normalizeOrganizationServerInput("http://localhost:3005/dashboard?x=1#y")).toBe(
      "http://localhost:3005",
    );
    expect(normalizeOrganizationServerInput("https://openwork.acme.com:8443/path")).toBe(
      "https://openwork.acme.com:8443",
    );
  });

  test("allows http only for loopback hosts", () => {
    expect(normalizeOrganizationServerInput("http://localhost:3005")).toBe(
      "http://localhost:3005",
    );
    expect(normalizeOrganizationServerInput("http://127.0.0.1")).toBe(
      "http://127.0.0.1",
    );
    expect(normalizeOrganizationServerInput("http://127.42.7.9:8080")).toBe(
      "http://127.42.7.9:8080",
    );
    expect(normalizeOrganizationServerInput("http://[::1]:3005")).toBe(
      "http://[::1]:3005",
    );
    expect(normalizeOrganizationServerInput("http://openwork.acme.com")).toBeNull();
    expect(normalizeOrganizationServerInput("http://den.internal:8080")).toBeNull();
  });

  test("keeps https available for non-loopback hosts", () => {
    expect(normalizeOrganizationServerInput("https://openwork.acme.com")).toBe(
      "https://openwork.acme.com",
    );
    expect(normalizeOrganizationServerInput("https://den.internal:8080/path")).toBe(
      "https://den.internal:8080",
    );
  });

  test("rejects unsupported schemes, empty values, and malformed input", () => {
    expect(normalizeOrganizationServerInput("ftp://openwork.acme.com")).toBeNull();
    expect(normalizeOrganizationServerInput("")).toBeNull();
    expect(normalizeOrganizationServerInput("not a url at all")).toBeNull();
    expect(normalizeOrganizationServerInput("https://")).toBeNull();
  });

  test("rejects URL-parser userinfo and backslash oddities", () => {
    expect(normalizeOrganizationServerInput("https://admin@openwork.acme.com")).toBeNull();
    expect(normalizeOrganizationServerInput("https://admin:secret@openwork.acme.com/path")).toBeNull();
    expect(normalizeOrganizationServerInput("https:\\openwork.acme.com\\dashboard")).toBeNull();
    expect(normalizeOrganizationServerInput("openwork.acme.com\\@attacker.example")).toBeNull();
  });
});
