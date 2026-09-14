import axios from 'axios'

const API_BASE_URL = '/api'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ==================== 系统状态 API ====================

export const systemApi = {
  // 获取系统状态
  getStatus: () => api.get('/system/status'),
  
  // 获取系统统计
  getStats: () => api.get('/system/stats'),
  
  // 获取工具状态
  getTools: () => api.get('/system/tools'),
}

// ==================== 目标管理 API ====================

export const targetApi = {
  // 获取目标列表
  list: () => api.get('/targets'),
  
  // 创建目标
  create: (data: { name: string; ip: string; description?: string }) => 
    api.post('/targets', data),
  
  // 删除目标
  delete: (id: string) => api.delete(`/targets/${id}`),
}

// ==================== 扫描任务 API ====================

export const scanApi = {
  // 启动扫描
  start: (data: {
    target: string
    scan_type: string
    phases: string[]
    depth: string
    timeout: number
  }) => api.post('/scan/start', data),
  
  // 获取任务列表
  listTasks: () => api.get('/scan/tasks'),
  
  // 获取任务详情
  getTask: (taskId: string) => api.get(`/scan/task/${taskId}`),
  
  // 取消任务
  cancel: (taskId: string) => api.delete(`/scan/task/${taskId}`),
}

// ==================== 漏洞管理 API ====================

export const vulnerabilityApi = {
  // 获取漏洞列表
  list: (params?: { severity?: string; status?: string; search?: string }) => 
    api.get('/vulnerabilities', { params }),
  
  // 获取漏洞统计
  getStats: () => api.get('/vulnerabilities/stats'),
}

// ==================== 报告 API ====================

export const reportApi = {
  // 获取报告列表
  list: () => api.get('/reports'),
  
  // 获取报告详情
  get: (taskId: string, format?: string) => 
    api.get(`/reports/${taskId}`, { params: { format } }),
  
  // 下载报告
  download: (taskId: string, format: string) => 
    `${API_BASE_URL}/reports/${taskId}/download?format=${format}`,
}

// ==================== Agent API ====================

export const agentApi = {
  // 获取Agent状态
  getStatus: () => api.get('/agents/status'),
  
  // 获取Agent活动记录
  getActivities: (limit?: number) => 
    api.get('/agents/activities', { params: { limit } }),
}

// ==================== 会话观测 API ====================

export const sessionApi = {
  // 获取交互会话列表
  list: () => api.get('/sessions'),

  // 获取单个会话摘要
  get: (sessionId: string) => api.get(`/sessions/${sessionId}`),

  // 获取会话事件
  getEvents: (sessionId: string, limit?: number) =>
    api.get(`/sessions/${sessionId}/events`, { params: { limit } }),

  // 获取会话轮次
  getRounds: (sessionId: string) =>
    api.get(`/sessions/${sessionId}/rounds`),

  // 获取轮次消息
  getRoundMessages: (sessionId: string, roundId: string) =>
    api.get(`/sessions/${sessionId}/rounds/${roundId}/messages`),

  // 获取会话时间线
  getTimeline: (sessionId: string, limit?: number) =>
    api.get(`/sessions/${sessionId}/timeline`, { params: { limit } }),
}

export const createSessionEventsWebSocket = (sessionId: string): WebSocket => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${window.location.host}/ws/sessions/${sessionId}/events`
  return new WebSocket(url)
}

// ==================== 模型配置 API ====================

export const modelApi = {
  // 获取支持的模型提供商
  getProviders: () => api.get('/models/providers'),
  
  // 获取所有Agent的模型配置
  getConfig: () => api.get('/models/config'),
  
  // 获取Agent模型列表
  getAgents: () => api.get('/models/agents'),
  
  // 更新Agent模型配置
  updateAgent: (agentName: string, data: {
    provider: string
    model_name: string
    api_key?: string
    base_url?: string
    temperature?: number
    max_tokens?: number
    timeout?: number
  }) => api.put(`/models/agents/${agentName}`, data),
  
  // 测试Agent模型连接
  testConnection: (agentName: string) => 
    api.post(`/models/test/${agentName}`),
  
  // 启用/禁用Agent
  toggleAgent: (agentName: string, enabled: boolean) => 
    api.post(`/models/agents/${agentName}/toggle`, null, { params: { enabled } }),
}

// ==================== 团队 API ====================

export const teamApi = {
  // 获取团队状态
  getStatus: () => api.get('/team/status'),
}

// ==================== 配置 API ====================

export const configApi = {
  // 获取配置
  get: () => api.get('/config'),
  
  // 更新配置
  update: (data: {
    llm_provider?: string
    api_keys?: Record<string, string>
    temperature?: number
    max_tokens?: number
  }) => api.put('/config', data),
}

// ==================== 活动日志 API ====================

export const activityApi = {
  // 获取活动日志
  list: (limit?: number) => api.get('/activities', { params: { limit } }),
}

export default api
