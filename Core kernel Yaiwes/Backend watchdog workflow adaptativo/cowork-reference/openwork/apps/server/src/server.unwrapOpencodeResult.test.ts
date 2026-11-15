import { describe, expect, test } from "bun:test";

import { ApiError } from "./errors.js";
import { unwrapOpencodeResult } from "./server.js";

function captureFailure(run: () => unknown): unknown {
  try {
    run();
    return null;
  } catch (error) {
    return error;
  }
}

describe("unwrapOpencodeResult", () => {
  test("maps an error without a response to opencode_unreachable", () => {
    const error = { message: "fetch failed" };
    const failure = captureFailure(() => unwrapOpencodeResult({ data: undefined, error }, "/session"));

    expect(failure).toBeInstanceOf(ApiError);
    expect(failure).toMatchObject({
      status: 502,
      code: "opencode_unreachable",
      details: { body: error, path: "/session" },
    });
  });

  test("maps an error with a response to opencode_request_failed", () => {
    const error = { message: "bad gateway" };
    const failure = captureFailure(() => unwrapOpencodeResult({
      data: undefined,
      error,
      response: new Response(null, { status: 503 }),
    }, "/session"));

    expect(failure).toBeInstanceOf(ApiError);
    expect(failure).toMatchObject({
      status: 502,
      code: "opencode_request_failed",
      details: { status: 503, body: error, path: "/session" },
    });
  });

  test("returns data unchanged", () => {
    const data = { id: "session-1" };
    expect(unwrapOpencodeResult({ data, error: undefined, response: new Response() }, "/session")).toBe(data);
  });

  test("maps a result with neither data nor error to opencode_empty_response", () => {
    const failure = captureFailure(() => unwrapOpencodeResult({
      data: undefined,
      error: undefined,
      response: new Response(),
    }, "/session"));

    expect(failure).toBeInstanceOf(ApiError);
    expect(failure).toMatchObject({ status: 502, code: "opencode_empty_response" });
  });
});
