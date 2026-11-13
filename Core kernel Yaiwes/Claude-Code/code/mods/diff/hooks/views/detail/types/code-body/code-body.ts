import type { CodeBlock } from '../code-block'

/**
 * A file's hunks as the body draws them: the `Code` blocks in order, and
 * whether the body's budget or a source's cap left any of a line out.
 */
export type CodeBody = {
  blocks: readonly CodeBlock[]
  isTruncated: boolean
}
