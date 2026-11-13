import { expect, test } from "bun:test";
import {
  getDesktopGrant,
  getDesktopHandoffGrant,
  getDesktopHandoffOpenworkUrl,
} from "../app/(den)/_lib/desktop-handoff";

test("preserves the complete OpenWork desktop handoff URL", () => {
  const openworkUrl = "openwork://den-auth?grant=one-time-code&denBaseUrl=https%3A%2F%2Fapi.example.test";
  const payload = { grant: "one-time-code", openworkUrl };

  expect(getDesktopHandoffOpenworkUrl(payload)).toBe(openworkUrl);
  expect(getDesktopHandoffGrant(payload, openworkUrl)).toBe("one-time-code");
});

test("extracts a one-time grant from an OpenWork desktop handoff", () => {
  expect(
    getDesktopGrant(
      "openwork://den-auth?grant=one-time-code&baseUrl=https%3A%2F%2Fapi.example.test"
    )
  ).toBe("one-time-code");
});

test("rejects missing and malformed desktop handoffs", () => {
  expect(
    getDesktopGrant(
      "openwork://den-auth?baseUrl=https%3A%2F%2Fapi.example.test"
    )
  ).toBeNull();
  expect(getDesktopGrant("not a url")).toBeNull();
  expect(getDesktopGrant(null)).toBeNull();
});
