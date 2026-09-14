/**
 * What the pane's Buttons and Selects do, each closing over the plugin's
 * state in its register function.
 */
export type PaneActions = {
  /**
   * Shows this file's body under the list.
   */
  selectFile: (path: string) => void

  /**
   * Shows or hides the tests and generated files.
   */
  toggleNoise: () => void

  /**
   * Opens or closes the pre-session section.
   */
  togglePreSession: () => void

  /**
   * Picks the comparison base by its Select value; an unknown value is
   * ignored.
   */
  chooseBase: (value: string) => void

  /**
   * Picks the source by its Select value: `current` or a turn's number.
   */
  chooseSource: (value: string) => void

  /**
   * Arms this file's diff for the next prompt, or disarms it.
   */
  toggleAsk: (path: string) => void

  /**
   * Closes the pane as `/diff` closes it, the choice kept for the next
   * first edit.
   */
  close: () => void
}
