/**
 * One `Code` element of a file's body: its unified-diff source, and whether
 * a divider stands above it (it opens a hunk after another block).
 */
export type CodeBlock = {
  source: string
  hasDivider: boolean
}
