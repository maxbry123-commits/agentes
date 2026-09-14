import * as vscode from "vscode";

export class CodeLensProvider implements vscode.CodeLensProvider {
  provideCodeLenses(document: vscode.TextDocument): vscode.CodeLens[] {
    const lenses: vscode.CodeLens[] = [];
    const text = document.getText();

    const patterns = [
      /^(export\s+)?(async\s+)?function\s+\w+/gm,
      /^(public|private|protected|async)\s+\w+\s*\(/gm,
      /^def\s+\w+/gm,
      /^(pub\s+)?fn\s+\w+/gm,
      /^class\s+\w+/gm,
    ];

    for (const pattern of patterns) {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        const pos = document.positionAt(match.index);
        const range = new vscode.Range(pos, pos);
        lenses.push(
          new vscode.CodeLens(range, { title: "$(symbol-method) Erkl\u00e4ren", command: "cognithor.explainCode", arguments: [{ range }] }),
          new vscode.CodeLens(range, { title: "Refactoren", command: "cognithor.refactorCode", arguments: [{ range }] }),
          new vscode.CodeLens(range, { title: "Tests", command: "cognithor.generateTests", arguments: [{ range }] })
        );
      }
    }
    return lenses;
  }
}
