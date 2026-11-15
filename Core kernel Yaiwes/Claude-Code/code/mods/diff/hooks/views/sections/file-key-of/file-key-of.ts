import Layout from '../../layout'

/**
 * A file row's Button address: the path made printable, under `file:`.
 *
 * @param path the file's path as git or the transcript gave it
 * @returns the key
 */
export const fileKeyOf = (path: string) => `file:${Layout.sanitizeName(path)}`
