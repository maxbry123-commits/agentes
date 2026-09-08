import { afterEach, describe, expect, jest, test } from "bun:test";

import {
  classifySessionTitleRecoveryRead,
  createSessionTitleRecovery,
  type SessionTitleRecoveryRead,
} from "../src/react-app/domains/session/sync/session-title-recovery";

const placeholder = "New session - 2026-08-11T10:00:00.000Z";

function read(
  title: string,
  messages: SessionTitleRecoveryRead["messages"] = [],
): SessionTitleRecoveryRead {
  return { title, messages };
}

const user = { role: "user", synthetic: false, error: undefined };
const assistant = { role: "assistant", synthetic: false, error: undefined };

async function flushMicrotasks() {
  for (let index = 0; index < 5; index += 1) await Promise.resolve();
}

afterEach(() => {
  jest.useRealTimers();
});

describe("session title recovery", () => {
  test("classifies only a successful first turn with a generated placeholder as failed", () => {
    expect(classifySessionTitleRecoveryRead(read(placeholder, [user, assistant]))).toBe("failed");
    expect(classifySessionTitleRecoveryRead(read("Useful title", [user, assistant]))).toBe("resolved");
    expect(classifySessionTitleRecoveryRead(read(placeholder, [user, assistant, user, assistant]))).toBe("not-applicable");
    expect(classifySessionTitleRecoveryRead(read(placeholder, [user, { ...assistant, error: { message: "denied" } }]))).toBe("pending");
  });

  test("refreshes until a slow generated title resolves", async () => {
    jest.useFakeTimers();
    const fetched = [
      read(placeholder, [user, assistant]),
      read("Investigate title access", [user, assistant]),
    ];
    const resolved: string[] = [];
    let failures = 0;
    const recovery = createSessionTitleRecovery({
      delaysMs: [10, 20, 30],
      fetch: async () => fetched.shift() ?? read("Investigate title access", [user, assistant]),
      onResolved: (_sessionId, title) => resolved.push(title),
      onFailure: () => { failures += 1; },
    });

    recovery.observe("session-a");
    jest.advanceTimersByTime(10);
    await flushMicrotasks();
    jest.advanceTimersByTime(20);
    await flushMicrotasks();

    expect(resolved).toEqual(["Investigate title access"]);
    expect(failures).toBe(0);
    recovery.dispose();
  });

  test("warns once after the final confirmed placeholder", async () => {
    jest.useFakeTimers();
    let fetches = 0;
    const failures: string[] = [];
    const recovery = createSessionTitleRecovery({
      delaysMs: [10, 20, 30],
      fetch: async () => {
        fetches += 1;
        return read(placeholder, [user, assistant]);
      },
      onResolved: () => {},
      onFailure: (sessionId) => failures.push(sessionId),
    });

    recovery.observe("session-a");
    recovery.observe("session-a");
    jest.advanceTimersByTime(10);
    await flushMicrotasks();
    jest.advanceTimersByTime(20);
    await flushMicrotasks();
    jest.advanceTimersByTime(30);
    await flushMicrotasks();
    recovery.observe("session-a");
    jest.advanceTimersByTime(100);
    await flushMicrotasks();

    expect(fetches).toBe(3);
    expect(failures).toEqual(["session-a"]);
    recovery.dispose();
  });

  test("cancels pending probes when an update supplies a title", async () => {
    jest.useFakeTimers();
    let fetches = 0;
    const recovery = createSessionTitleRecovery({
      delaysMs: [10],
      fetch: async () => {
        fetches += 1;
        return read(placeholder, [user, assistant]);
      },
      onResolved: () => {},
      onFailure: () => {},
    });

    recovery.observe("session-a");
    recovery.resolve("session-a");
    jest.advanceTimersByTime(10);
    await flushMicrotasks();

    expect(fetches).toBe(0);
    recovery.dispose();
  });
});
