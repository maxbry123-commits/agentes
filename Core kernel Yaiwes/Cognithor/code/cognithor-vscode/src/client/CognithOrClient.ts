export interface ClientConfig {
  serverUrl: string;
  streaming: boolean;
  timeout?: number;
}

export interface ChatRequest {
  message: string;
  context?: CodeContext;
  sessionId?: string;
}

export interface CodeContext {
  filePath: string;
  language: string;
  selectedCode?: string;
  surroundingCode?: string;
  cursorLine?: number;
  projectFiles?: string[];
}

export interface ChatResponse {
  message: string;
  codeBlocks?: { language: string; code: string; explanation?: string }[];
  model: string;
  tokenCount: number;
  sessionId: string;
}

export class CognithOrClient {
  private config: ClientConfig;
  private sessionId: string;

  constructor(config: ClientConfig) {
    this.config = config;
    this.sessionId = `vscode_${Date.now()}`;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(`${this.config.serverUrl}/api/v1/health`, {
        signal: controller.signal,
      });
      clearTimeout(timeout);
      return res.ok;
    } catch {
      return false;
    }
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${this.config.serverUrl}/api/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...request,
        sessionId: request.sessionId || this.sessionId,
      }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Cognithor API error ${res.status}: ${text}`);
    }
    return res.json();
  }

  chatStream(
    request: ChatRequest,
    onToken: (token: string) => void,
    onComplete: (response: ChatResponse) => void,
    onError: (error: Error) => void
  ): () => void {
    const wsUrl = this.config.serverUrl
      .replace("http://", "ws://")
      .replace("https://", "wss://");

    const WebSocket = require("ws");
    const ws = new WebSocket(`${wsUrl}/ws/${this.sessionId}`);

    ws.on("open", () => {
      // Auth
      ws.send(JSON.stringify({ type: "auth", token: "" }));
      // Then message
      setTimeout(() => {
        ws.send(JSON.stringify({
          type: "user_message",
          text: request.message,
          session_id: this.sessionId,
        }));
      }, 100);
    });

    ws.on("message", (data: Buffer) => {
      try {
        const msg = JSON.parse(data.toString());
        if (msg.type === "stream_token") onToken(msg.token);
        else if (msg.type === "assistant_message") {
          onComplete({
            message: msg.text,
            model: msg.model || "unknown",
            tokenCount: msg.token_count || 0,
            sessionId: this.sessionId,
          });
        }
        else if (msg.type === "error") onError(new Error(msg.error));
      } catch {}
    });

    ws.on("error", () => onError(new Error("WebSocket error")));

    return () => { try { ws.close(); } catch {} };
  }

  disconnect() {}
}
