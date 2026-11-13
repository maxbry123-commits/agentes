import * as vscode from "vscode";
import { CognithOrClient } from "./client/CognithOrClient";
import { ChatViewProvider } from "./providers/ChatViewProvider";
import { CodeLensProvider } from "./providers/CodeLensProvider";
import { ContextManager } from "./context/ContextManager";

let client: CognithOrClient | undefined;

export async function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration("cognithor");

  client = new CognithOrClient({
    serverUrl: config.get("serverUrl") || "http://localhost:8741",
    streaming: config.get("streamingEnabled") !== false,
  });

  // Health check
  const connected = await client.healthCheck();
  if (connected) {
    vscode.window.showInformationMessage("Cognithor verbunden");
  } else {
    const action = await vscode.window.showWarningMessage(
      "Cognithor nicht erreichbar. Bitte Cognithor starten.",
      "Einstellungen"
    );
    if (action === "Einstellungen") {
      vscode.commands.executeCommand("workbench.action.openSettings", "cognithor");
    }
  }

  // Chat sidebar
  const chatProvider = new ChatViewProvider(context.extensionUri, client);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("cognithor.chatView", chatProvider)
  );

  // Code Lens
  if (config.get("codeLens") !== false) {
    context.subscriptions.push(
      vscode.languages.registerCodeLensProvider({ scheme: "file" }, new CodeLensProvider())
    );
  }

  // Commands
  const commands: [string, (...args: any[]) => any][] = [
    ["cognithor.chat", () => vscode.commands.executeCommand("cognithor.chatView.focus")],
    ["cognithor.explainCode", () => sendWithContext(client!, "Erkläre diesen Code:", chatProvider)],
    ["cognithor.refactorCode", () => sendWithContext(client!, "Refactore diesen Code:", chatProvider)],
    ["cognithor.fixBug", () => sendWithContext(client!, "Finde und fixe Bugs in diesem Code:", chatProvider)],
    ["cognithor.generateTests", () => sendWithContext(client!, "Generiere Tests für diesen Code:", chatProvider)],
    ["cognithor.generateDocs", () => sendWithContext(client!, "Generiere Dokumentation für diesen Code:", chatProvider)],
    ["cognithor.generateCode", async () => {
      const prompt = await vscode.window.showInputBox({ prompt: "Was soll generiert werden?" });
      if (prompt) chatProvider.sendMessage(prompt);
    }],
    ["cognithor.addToContext", () => {
      const editor = vscode.window.activeTextEditor;
      if (editor) vscode.window.showInformationMessage(`${editor.document.fileName} zum Kontext hinzugefügt`);
    }],
    ["cognithor.clearContext", () => vscode.window.showInformationMessage("Kontext geleert")],
    ["cognithor.openSettings", () => vscode.commands.executeCommand("workbench.action.openSettings", "cognithor")],
    ["cognithor.reconnect", async () => {
      const ok = await client?.healthCheck();
      vscode.window.showInformationMessage(ok ? "Cognithor verbunden" : "Verbindung fehlgeschlagen");
    }],
  ];

  for (const [id, handler] of commands) {
    context.subscriptions.push(vscode.commands.registerCommand(id, handler));
  }
}

async function sendWithContext(client: CognithOrClient, prefix: string, chatProvider: ChatViewProvider) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("Kein aktiver Editor");
    return;
  }
  const selection = editor.selection;
  const selectedCode = editor.document.getText(selection.isEmpty ? undefined : selection);
  const message = `${prefix}\n\n\`\`\`${editor.document.languageId}\n${selectedCode.slice(0, 3000)}\n\`\`\``;
  chatProvider.sendMessage(message);
}

export function deactivate() {
  client?.disconnect();
}
