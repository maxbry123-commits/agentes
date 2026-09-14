declare const describe: (name: string, fn: () => void) => void;
declare const test: (name: string, fn: () => void) => void;
declare const expect: (value: unknown) => {
  toEqual: (expected: unknown) => void;
};

import { filterCloudManagedModelOptions } from "@/react-app/domains/connections/provider-auth/assigned-model-options";

describe("filterCloudManagedModelOptions", () => {
  const options = [
    { providerID: "openwork", modelID: "cloud-model" },
    { providerID: "lpr_team", modelID: "managed-model" },
    { providerID: "anthropic", modelID: "local-model" },
  ];

  test("hides cached cloud providers after logout", () => {
    expect(filterCloudManagedModelOptions(options, false)).toEqual([
      { providerID: "anthropic", modelID: "local-model" },
    ]);
  });

  test("retains cloud providers while signed in", () => {
    expect(filterCloudManagedModelOptions(options, true)).toEqual(options);
  });
});
