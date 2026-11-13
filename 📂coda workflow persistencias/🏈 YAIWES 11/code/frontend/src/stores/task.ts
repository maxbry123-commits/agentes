import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { TaskWebSocket } from '@/utils/websocket'
import api from '@/utils/request'
import type { AnyMessage, SolveStepMessage, SystemMessage, ApprovalMessage } from '@/utils/interface'

export const useTaskStore = defineStore('task', () => {
  // State
  const messages = ref<AnyMessage[]>([])
  const currentTaskId = ref<string | null>(null)
  const wsConnected = ref(false)
  const approvalCallback = ref<((msg: ApprovalMessage) => void) | null>(null)

  let ws: TaskWebSocket | null = null

  // Getters
  const systemMessages = computed(() =>
    messages.value.filter((m): m is SystemMessage => m.msg_type === 'system')
  )
  const solveSteps = computed(() =>
    messages.value.filter((m): m is SolveStepMessage => m.msg_type === 'solve_step')
  )
  const latestStep = computed(() => solveSteps.value.at(-1) ?? null)
  const flagFound = computed(() => solveSteps.value.some((s) => s.flag_found))
  const flagValue = computed(() => solveSteps.value.find((s) => s.flag_found)?.flag_value ?? '')

  // Actions
  async function loadTaskMessages(taskId: string) {
    try {
      const { data } = await api.get(`/task/${taskId}/messages`)
      if (data.messages) {
        messages.value = data.messages
      }
    } catch (e) {
      console.warn('Failed to load messages:', e)
    }
  }

  function connectWebSocket(taskId: string) {
    currentTaskId.value = taskId
    ws?.close()

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${proto}//${location.host}/ws/task/${taskId}`
    ws = new TaskWebSocket(url, (data: unknown) => {
      const msg = data as AnyMessage
      // Dedup by id
      const exists = messages.value.some((m) => m.id === msg.id)
      if (!exists) {
        messages.value.push(msg)
      }
      // Approval callback
      if (msg.msg_type === 'approval' && approvalCallback.value) {
        approvalCallback.value(msg as ApprovalMessage)
      }
    })
    ws.connect()
    wsConnected.value = true
  }

  function sendDecision(checkpointId: string, decision: Record<string, unknown>) {
    ws?.send({ type: 'user_decision', checkpoint_id: checkpointId, decision })
  }

  function closeWebSocket() {
    ws?.close()
    wsConnected.value = false
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages, currentTaskId, wsConnected, approvalCallback,
    systemMessages, solveSteps, latestStep, flagFound, flagValue,
    loadTaskMessages, connectWebSocket, sendDecision, closeWebSocket, clearMessages,
  }
})
