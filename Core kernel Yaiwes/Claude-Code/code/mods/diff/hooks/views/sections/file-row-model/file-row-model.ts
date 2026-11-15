/**
 * One listed file as its row draws it: the Button's address, the path, the
 * counts or a dim note in their place, and whether its body shows.
 */
export type FileRowModel = {
  key: string
  path: string
  added: number
  removed: number
  note: string | null
  isSelected: boolean
}
