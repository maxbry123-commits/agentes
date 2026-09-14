type MessageHandler = (data: unknown) => void

export class TaskWebSocket {
  private socket: WebSocket | null = null
  private url: string
  private onMessage: MessageHandler
  private reconnectAttempts = 0
  private maxReconnect = 10
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  constructor(url: string, onMessage: MessageHandler) {
    this.url = url
    this.onMessage = onMessage
  }

  connect() {
    if (this.socket) this.close()
    this.socket = new WebSocket(this.url)
    this.socket.onopen = () => {
      console.log('[WS] connected:', this.url)
      this.reconnectAttempts = 0
    }
    this.socket.onclose = (e) => {
      console.log('[WS] closed:', e.code, e.reason)
      if (e.code !== 1000 && e.code !== 1008 && this.reconnectAttempts < this.maxReconnect) {
        const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000)
        this.reconnectAttempts++
        console.log(`[WS] reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
        this.reconnectTimer = setTimeout(() => this.connect(), delay)
      }
    }
    this.socket.onerror = () => { /* onclose handles cleanup */ }
    this.socket.onmessage = (e) => {
      try {
        this.onMessage(JSON.parse(e.data))
      } catch {
        console.warn('[WS] invalid json:', e.data.slice(0, 100))
      }
    }
  }

  send(data: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data))
    }
  }

  close() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.reconnectAttempts = this.maxReconnect // stop reconnecting
    if (this.socket) {
      this.socket.onclose = null
      this.socket.close(1000)
      this.socket = null
    }
  }
}
