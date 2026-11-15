// A tiled chat IS an open chat, so the two states can never be allowed to drift apart. Anything that
// closes chats drops their zones in the SAME reducer: an after-the-fact effect leaves a window where
// the card is tile-sized but wearing the collapsed skin, and on a busy machine that window has been
// measured at 17 seconds (the "fullscreen turns white" bug).
export function untileClosedChats(
  tiledCards: Record<string, string>,
  chatCardIds: string[],
  openChatIds: readonly string[],
): void {
  const open = new Set(openChatIds);
  for (const id of chatCardIds) {
    if (!open.has(id)) delete tiledCards[id];
  }
}
