import { normalizeDenTypeId } from "@openwork-ee/utils/typeid"

export function artifactViewResourceUri(artifactViewId: string, revisionId: string): string {
  const normalizedViewId = normalizeDenTypeId("artifactView", artifactViewId)
  const normalizedRevisionId = normalizeDenTypeId("artifactViewRevision", revisionId)
  return `ui://openwork/artifacts/${normalizedViewId}/views/${normalizedRevisionId}/index.html`
}

export function parseArtifactViewResourceUri(uri: string) {
  const match = /^ui:\/\/openwork\/artifacts\/([^/]+)\/views\/([^/]+)\/index\.html$/.exec(uri)
  if (!match?.[1] || !match[2]) return null
  try {
    return {
      artifactViewId: normalizeDenTypeId("artifactView", match[1]),
      revisionId: normalizeDenTypeId("artifactViewRevision", match[2]),
    }
  } catch {
    return null
  }
}
