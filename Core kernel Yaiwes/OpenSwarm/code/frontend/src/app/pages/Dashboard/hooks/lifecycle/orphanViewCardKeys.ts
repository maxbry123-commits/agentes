// A view card's record key is the bare output id ONLY for the primary; every extra instance is
// `${output_id}#N`. Reading the key as if it were an output id therefore pronounced every secondary
// instance dead on arrival and swept it off the canvas. Always resolve through output_id.
export function orphanViewCardKeys(
  viewCards: Readonly<Record<string, { output_id: string }>>,
  outputs: Readonly<Record<string, unknown>>,
): string[] {
  return Object.entries(viewCards)
    .filter(([, card]) => !outputs[card.output_id])
    .map(([cardKey]) => cardKey);
}
