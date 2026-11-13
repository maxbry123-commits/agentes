export type ConnectorEffort = "guided" | "one_click" | "api_key" | "oauth_app" | "instant";

export function presetEffort(preset: {
  authType: string;
  requiresOAuthClient?: boolean;
}): ConnectorEffort {
  if (preset.authType === "none") return "instant";
  if (preset.authType === "apikey") return "api_key";
  if (preset.authType === "oauth" && preset.requiresOAuthClient) return "oauth_app";
  return "one_click";
}

export const EFFORT_LABELS: Record<ConnectorEffort, string> = {
  guided: "Guided setup",
  one_click: "One-click",
  api_key: "API key",
  oauth_app: "OAuth app required",
  instant: "Instant — no sign-in",
};
