declare const describe: (name: string, fn: () => void) => void;
declare const test: (name: string, fn: () => void) => void;
declare const expect: (value: unknown) => {
  toBe: (expected: unknown) => void;
};

import { QueryClient } from "@tanstack/react-query";

import {
  clearProviderListQueries,
  providerListQueryKey,
} from "./provider-list-query";

describe("clearProviderListQueries", () => {
  test("removes every workspace provider cache without touching unrelated queries", () => {
    const queryClient = new QueryClient();
    const firstProviderKey = providerListQueryKey({
      baseUrl: "http://127.0.0.1:4096",
      directory: "/workspace/one",
    });
    const secondProviderKey = providerListQueryKey({
      baseUrl: "http://127.0.0.1:4097",
      directory: "/workspace/two",
    });
    const unrelatedKey = ["workspaces"] as const;
    const unrelatedValue = ["workspace"];

    queryClient.setQueryData(firstProviderKey, { all: ["openwork"] });
    queryClient.setQueryData(secondProviderKey, { all: ["lpr_team"] });
    queryClient.setQueryData(unrelatedKey, unrelatedValue);

    clearProviderListQueries(queryClient);

    expect(queryClient.getQueryData(firstProviderKey)).toBe(undefined);
    expect(queryClient.getQueryData(secondProviderKey)).toBe(undefined);
    expect(queryClient.getQueryData(unrelatedKey)).toBe(unrelatedValue);
  });
});
