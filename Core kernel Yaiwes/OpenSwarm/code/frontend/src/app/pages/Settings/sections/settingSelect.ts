// The data-select-* handle that makes a Settings row pointable by the chat element-selector. One source for it, spread onto a row's Box, so a row's label and its selection metadata can't drift apart (same args) and every section opts in the same way instead of copy-pasting the JSON.stringify.
export function settingSelectAttrs(field: string, name: string, category: string, description?: string) {
  return {
    'data-select-type': 'settings-option',
    'data-select-id': field,
    'data-select-meta': JSON.stringify({ name, category, fieldName: field, description }),
  };
}
