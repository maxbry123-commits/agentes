import * as vscode from "vscode";

export interface CodeContext {
  filePath: string;
  language: string;
  selectedCode?: string;
  surroundingCode?: string;
  cursorLine?: number;
  projectFiles?: string[];
}

export class ContextManager {
  static buildFromEditor(editor: vscode.TextEditor | undefined): CodeContext | undefined {
    if (!editor) return undefined;

    const doc = editor.document;
    const selection = editor.selection;
    const config = vscode.workspace.getConfiguration("cognithor");
    const contextLines = (config.get("contextLines") as number) || 100;

    const selectedCode = !selection.isEmpty ? doc.getText(selection) : undefined;

    const cursorLine = selection.active.line;
    const startLine = Math.max(0, cursorLine - contextLines);
    const endLine = Math.min(doc.lineCount - 1, cursorLine + contextLines);
    const surroundingRange = new vscode.Range(
      new vscode.Position(startLine, 0),
      new vscode.Position(endLine, doc.lineAt(endLine).text.length)
    );

    return {
      filePath: doc.uri.fsPath,
      language: doc.languageId,
      selectedCode,
      surroundingCode: doc.getText(surroundingRange),
      cursorLine,
      projectFiles: vscode.workspace.textDocuments
        .filter((d) => !d.isUntitled && d.uri.scheme === "file")
        .map((d) => d.uri.fsPath)
        .slice(0, 20),
    };
  }
}
