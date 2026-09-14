import { describe, expect, test } from "bun:test";

import { sendWithRevertRollback } from "../src/react-app/domains/session/surface/safe-edit-resend";

describe("safe edit resend", () => {
  test("sends a normal draft without history mutation", async () => {
    const calls: string[] = [];
    await sendWithRevertRollback({
      abort: async () => calls.push("abort"),
      revert: async () => calls.push("revert"),
      prompt: async () => { calls.push("prompt"); },
      unrevert: async () => calls.push("unrevert"),
    });

    expect(calls).toEqual(["prompt"]);
  });

  test("orders revert before prompt and unreverts a failed replacement", async () => {
    const calls: string[] = [];
    const promptError = new Error("prompt dispatch failed");
    let thrown: unknown;

    try {
      await sendWithRevertRollback({
        revertMessageId: "message-a",
        abort: async () => calls.push("abort"),
        revert: async (messageId) => calls.push(`revert:${messageId}`),
        prompt: async () => {
          calls.push("prompt");
          throw promptError;
        },
        unrevert: async () => calls.push("unrevert"),
      });
    } catch (error) {
      thrown = error;
    }

    expect(calls).toEqual(["abort", "revert:message-a", "prompt", "unrevert"]);
    expect(thrown).toBe(promptError);
  });
});
