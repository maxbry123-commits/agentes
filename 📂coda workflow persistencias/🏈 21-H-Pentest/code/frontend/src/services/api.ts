/**
 * API服务 - 适配后端API
 */
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

// ============ Types ============
export interface Task {
  id: string
  target_url: string
  mode: string
  status: string
  created_at: string
  started_at?: string
  completed_at?: string
  finished_at?: string
  max_rounds: number
  current_round: number
  flags_found: string[]
  flags: string[]
  vulnerabilities: any[]
  report?: any
  task_plan?: any
}

export interface CreateTaskRequest {
  target_url: string
  mode: string
  max_rounds: number
  model: string
}

export interface InterventionRequest {
  action: 'pause' | 'resume' | 'inject' | 'force_stop'
  instruction?: string
  priority?: string
}

export interface Message {
  id: string
  task_id: string
  type: string
  content: string
  metadata: any
  round?: number
  created_at: string
}

export interface Conversation {
  id: string
  task_id: string
  role: string
  content: string
  round: number
  created_at: string
}

// ============ Tasks API ============
export const tasksApi = {
  // 创建任务
  async create(request: CreateTaskRequest): Promise<Task> {
    const { data } = await axios.post(`${API_BASE_URL}/tasks/`, request)
    return data
  },

  // 获取任务列表
  async list(skip = 0, limit = 10): Promise<Task[]> {
    const { data } = await axios.get(`${API_BASE_URL}/tasks/`, {
      params: { skip, limit }
    })
    return data
  },

  // 获取任务详情
  async get(taskId: string): Promise<Task> {
    const { data } = await axios.get(`${API_BASE_URL}/tasks/${taskId}`)
    return data
  },

  // 人工干预
  async intervene(taskId: string, request: InterventionRequest) {
    const { data } = await axios.post(
      `${API_BASE_URL}/tasks/${taskId}/intervention`,
      request
    )
    return data
  },

  // 停止任务
  async stop(taskId: string, force = false) {
    const { data } = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stop`, null, {
      params: { force }
    })
    return data
  },

  // 删除任务
  async delete(taskId: string) {
    const { data } = await axios.delete(`${API_BASE_URL}/tasks/${taskId}`)
    return data
  }
}

// ============ Messages API ============
export const messagesApi = {
  // 获取消息列表
  async list(
    taskId: string,
    skip = 0,
    limit = 100,
    msgType?: string
  ): Promise<Message[]> {
    const { data } = await axios.get(`${API_BASE_URL}/tasks/${taskId}/messages`, {
      params: { skip, limit, msg_type: msgType }
    })
    return data
  },

  // 获取最新消息（增量轮询）
  async getLatest(taskId: string, since?: string): Promise<Message[]> {
    const { data } = await axios.get(
      `${API_BASE_URL}/tasks/${taskId}/messages/latest`,
      {
        params: { since }
      }
    )
    return data
  }
}

// ============ Conversations API ============
export const conversationsApi = {
  // 获取对话历史
  async list(
    taskId: string,
    skip = 0,
    limit = 100
  ): Promise<Conversation[]> {
    const { data } = await axios.get(
      `${API_BASE_URL}/tasks/${taskId}/conversations`,
      {
        params: { skip, limit }
      }
    )
    return data
  }
}
