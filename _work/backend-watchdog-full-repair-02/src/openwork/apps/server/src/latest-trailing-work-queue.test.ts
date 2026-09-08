import { describe, expect, test } from "bun:test";

import { LatestTrailingWorkQueue } from "./latest-trailing-work-queue.js";

describe("LatestTrailingWorkQueue", () => {
  test("coalesces arrivals during an active pass into one latest-value trailing pass", async () => {
    let releaseFirst: () => void = () => undefined;
    const firstReleased = new Promise<void>((resolve) => {
      releaseFirst = resolve;
    });
    let markFirstReached: () => void = () => undefined;
    const firstReached = new Promise<void>((resolve) => {
      markFirstReached = resolve;
    });
    const values: number[] = [];
    let active = 0;
    let maxActive = 0;
    const queue = new LatestTrailingWorkQueue<string, number>(async (value) => {
      values.push(value);
      active += 1;
      maxActive = Math.max(maxActive, active);
      try {
        if (value === 1) {
          markFirstReached();
          await firstReleased;
        }
      } finally {
        active -= 1;
      }
    }, () => undefined);

    const first = queue.enqueue("workspace", 1);
    await firstReached;
    const superseded = queue.enqueue("workspace", 2);
    const latest = queue.enqueue("workspace", 3);
    expect(values).toEqual([1]);

    releaseFirst();
    await Promise.all([first, superseded, latest]);
    expect(values).toEqual([1, 3]);
    expect(maxActive).toBe(1);
  });

  test("continues with trailing and later work after a rejected pass", async () => {
    let releaseFirst: () => void = () => undefined;
    const firstReleased = new Promise<void>((resolve) => {
      releaseFirst = resolve;
    });
    let markFirstReached: () => void = () => undefined;
    const firstReached = new Promise<void>((resolve) => {
      markFirstReached = resolve;
    });
    const values: number[] = [];
    const detachedErrors: unknown[] = [];
    const queue = new LatestTrailingWorkQueue<string, number>(async (value) => {
      values.push(value);
      if (value !== 1) return;
      markFirstReached();
      await firstReleased;
      throw new Error("first pass failed");
    }, (_key, error) => detachedErrors.push(error));

    const first = queue.enqueue("workspace", 1);
    await firstReached;
    const trailing = queue.enqueue("workspace", 2);
    releaseFirst();

    await expect(first).rejects.toThrow("first pass failed");
    await trailing;
    await queue.enqueue("workspace", 3);
    expect(values).toEqual([1, 2, 3]);
    expect(detachedErrors).toEqual([]);
  });
});
