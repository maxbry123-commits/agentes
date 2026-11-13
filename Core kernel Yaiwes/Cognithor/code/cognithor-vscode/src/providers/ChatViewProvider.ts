import * as vscode from "vscode";
import { CognithOrClient } from "../client/CognithOrClient";
import { ContextManager } from "../context/ContextManager";

export class ChatViewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "cognithor.chatView";
  private view?: vscode.WebviewView;
  private cancelStream?: () => void;

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly client: CognithOrClient
  ) {}

  resolveWebviewView(webviewView: vscode.WebviewView) {
    this.view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };
    webviewView.webview.html = this.getHtml();

    webviewView.webview.onDidReceiveMessage(async (data: any) => {
      if (data.type === "sendMessage") await this.handleChat(data.text);
      else if (data.type === "cancelStream") this.cancelStream?.();
      else if (data.type === "insertCode") await this.insertCode(data.code);
    });
  }

  async sendMessage(text: string) {
    this.view?.webview.postMessage({ type: "userMessage", text });
    await this.handleChat(text);
  }

  private async handleChat(text: string) {
    const context = ContextManager.buildFromEditor(vscode.window.activeTextEditor);
    this.post({ type: "streamStart" });

    this.cancelStream = this.client.chatStream(
      { message: text, context },
      (token) => this.post({ type: "streamToken", token }),
      (response) => this.post({ type: "streamEnd", response }),
      (error) => this.post({ type: "error", message: error.message })
    );
  }

  private async insertCode(code: string) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    await editor.edit((eb) => {
      if (editor.selection.isEmpty) eb.insert(editor.selection.active, code);
      else eb.replace(editor.selection, code);
    });
  }

  private post(msg: object) {
    this.view?.webview.postMessage(msg);
  }

  private getHtml(): string {
    return `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); background: var(--vscode-sideBar-background); display: flex; flex-direction: column; height: 100vh; }
  #messages { flex: 1; overflow-y: auto; padding: 12px; }
  .msg { margin-bottom: 12px; padding: 8px 12px; border-radius: 8px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word; }
  .msg.user { background: var(--vscode-input-background); border: 1px solid var(--vscode-input-border); margin-left: 20%; }
  .msg.assistant { background: var(--vscode-editor-background); border-left: 3px solid var(--vscode-textLink-foreground); }
  .msg.error { background: var(--vscode-inputValidation-errorBackground); border-left: 3px solid var(--vscode-errorForeground); }
  .msg pre { background: var(--vscode-textCodeBlock-background); padding: 8px; border-radius: 4px; overflow-x: auto; margin: 8px 0; position: relative; }
  .msg code { font-family: var(--vscode-editor-font-family); font-size: var(--vscode-editor-font-size); }
  .insert-btn { position: absolute; top: 4px; right: 4px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 11px; }
  .insert-btn:hover { background: var(--vscode-button-hoverBackground); }
  #input-area { padding: 8px 12px; border-top: 1px solid var(--vscode-panel-border); display: flex; gap: 8px; }
  #input { flex: 1; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); padding: 8px; border-radius: 4px; font-family: var(--vscode-font-family); font-size: 13px; resize: none; }
  #input:focus { outline: 1px solid var(--vscode-focusBorder); }
  #send { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: 600; }
  #send:hover { background: var(--vscode-button-hoverBackground); }
  .typing { color: var(--vscode-descriptionForeground); font-style: italic; padding: 4px 12px; }
</style>
</head>
<body>
<div id="messages"></div>
<div id="input-area">
  <textarea id="input" rows="2" placeholder="Frage Cognithor..."></textarea>
  <button id="send">Senden</button>
</div>
<script>
  const vscode = acquireVsCodeApi();
  const messages = document.getElementById('messages');
  const input = document.getElementById('input');
  const send = document.getElementById('send');
  let streaming = false;
  let currentAssistant = null;

  send.addEventListener('click', () => sendMsg());
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
  });

  function sendMsg() {
    const text = input.value.trim();
    if (!text) return;
    addMessage('user', text);
    input.value = '';
    vscode.postMessage({ type: 'sendMessage', text });
  }

  function addMessage(role, text) {
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    div.innerHTML = formatMessage(text);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function formatMessage(text) {
    // Simple markdown: code blocks with insert buttons
    return text.replace(/\\\`\\\`\\\`(\\w*)\\n([\\s\\S]*?)\\\`\\\`\\\`/g, (_, lang, code) => {
      const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      return '<pre><code>' + escaped + '</code><button class="insert-btn" onclick="insertCode(this)">Einfuegen</button></pre>';
    }).replace(/\\\`([^\\\`]+)\\\`/g, '<code>$1</code>');
  }

  function insertCode(btn) {
    const code = btn.previousElementSibling.textContent;
    vscode.postMessage({ type: 'insertCode', code });
  }

  window.addEventListener('message', (event) => {
    const msg = event.data;
    if (msg.type === 'streamStart') {
      streaming = true;
      currentAssistant = addMessage('assistant', '');
      const typing = document.createElement('div');
      typing.className = 'typing';
      typing.id = 'typing';
      typing.textContent = 'Cognithor denkt nach...';
      messages.appendChild(typing);
    } else if (msg.type === 'streamToken' && currentAssistant) {
      document.getElementById('typing')?.remove();
      currentAssistant.innerHTML += msg.token;
      messages.scrollTop = messages.scrollHeight;
    } else if (msg.type === 'streamEnd') {
      document.getElementById('typing')?.remove();
      if (msg.response && currentAssistant) {
        currentAssistant.innerHTML = formatMessage(msg.response.message);
      }
      streaming = false;
      currentAssistant = null;
    } else if (msg.type === 'error') {
      document.getElementById('typing')?.remove();
      addMessage('error', msg.message);
      streaming = false;
    } else if (msg.type === 'userMessage') {
      addMessage('user', msg.text);
    }
  });
</script>
</body>
</html>`;
  }
}
