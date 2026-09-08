/**
 * Where a signed-in user lands. `/onboarding` owns organization resolution:
 * it runs when no active organization is committed yet, and also while a
 * desktop-initiated sign-in is deliberately holding the choice open for the
 * user (`orgSelectionPending`) — even if a background layer has already
 * written some default organization id.
 */
export function signedInRoute(
  activeOrgId: string | null | undefined,
  options?: { orgSelectionPending?: boolean },
): "/session" | "/onboarding" {
  if (options?.orgSelectionPending) return "/onboarding";
  return activeOrgId?.trim() ? "/session" : "/onboarding";
}
