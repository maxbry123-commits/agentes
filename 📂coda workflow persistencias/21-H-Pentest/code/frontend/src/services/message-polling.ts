/**
 * 消息轮询服务 - 适配新后端messages API
 */
import { messagesApi, type Message } from './api'

export class MessagePollingService {
  private taskId: string
  private pollingInterval: number
  private latestTimestamp: string | null = null
  private isPolling: boolean = false
  private timerId: number | null = null
  private onMessagesCallback: ((messages: Message[]) => void) | null = null
  private errorCount: number = 0
  private maxErrors: number = 20  // 🔥 增加到20次，避免轻易停止轮询

  constructor(taskId: string, pollingInterval: number = 3000) {
    this.taskId = taskId
    this.pollingInterval = pollingInterval
  }

  /**
   * 开始轮询
   */
  async start(onMessages: (messages: Message[]) => void) {
    if (this.isPolling) {
      console.warn('⚠️ 轮询已在进行中')
      return
    }

    this.onMessagesCallback = onMessages
    this.isPolling = true

    console.log(`🔄 开始轮询任务消息: ${this.taskId}, 间隔: ${this.pollingInterval}ms`)

    // 立即执行第一次轮询
    await this.poll()

    // 设置定时轮询
    this.timerId = window.setInterval(async () => {
      await this.poll()
    }, this.pollingInterval)
  }

  /**
   * 停止轮询
   */
  stop() {
    if (this.timerId !== null) {
      clearInterval(this.timerId)
      this.timerId = null
    }
    this.isPolling = false
    this.errorCount = 0
    console.log('🛑 停止轮询')
  }

  /**
   * 执行单次轮询
   */
  private async poll() {
    try {
      // 使用最新API获取增量消息
      const messages = await messagesApi.getLatest(
        this.taskId,
        this.latestTimestamp || undefined
      )

      // 成功后重置错误计数
      this.errorCount = 0

      // 更新最新时间戳
      if (messages.length > 0) {
        const latestMsg = messages[messages.length - 1]
        console.log(`🕒 更新时间戳: ${this.latestTimestamp} -> ${latestMsg.created_at}`)
        this.latestTimestamp = latestMsg.created_at

        console.log(`📨 收到 ${messages.length} 条新消息`)
        if (this.onMessagesCallback) {
          this.onMessagesCallback(messages)
        }
      }
    } catch (error: any) {
      // 任务不存在或已删除
      if (error.response?.status === 404) {
        console.warn('⚠️ 任务不存在，停止轮询')
        this.stop()
        return
      }

      this.errorCount++

      // 只在首次错误时打印
      if (this.errorCount === 1) {
        console.error('❌ 轮询出错:', error)
      }

      // 🔥🔥🔥 不再停止轮询，只记录错误，继续轮询
      // 网络抖动、后端暂时无响应都不影响轮询
    }
  }

  /**
   * 重置轮询（清空时间戳）
   */
  reset() {
    this.latestTimestamp = null
  }

  /**
   * 修改轮询间隔
   */
  setPollingInterval(interval: number) {
    this.pollingInterval = interval

    // 如果正在轮询，重启以应用新间隔
    if (this.isPolling && this.onMessagesCallback) {
      this.stop()
      this.start(this.onMessagesCallback)
    }
  }
}
