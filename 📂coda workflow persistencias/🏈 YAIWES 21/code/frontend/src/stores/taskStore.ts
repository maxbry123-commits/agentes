// Pinia任务状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  WebSocketMessage, 
  LogMessage, 
  ProgressMessage, 
  ToolExecutionMessage,
  VulnerabilityMessage,
  FlagMessage 
} from '@/services/websocket'

export interface Task {
  id: string
  target_url: string
  mode: 'ctf' | 'realworld'
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  current_round: number
  max_rounds: number
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface Vulnerability {
  type: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  description: string
  url: string
  evidence?: string
  discovered_at: string
}

export interface ToolExecution {
  tool_name: string
  arguments: Record<string, any>
  result: string
  execution_time?: number
  timestamp: string
}

export interface LogEntry {
  log_type: 'info' | 'warning' | 'error' | 'success' | 'debug'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

export const useTaskStore = defineStore('task', () => {
  // 当前任务
  const currentTask = ref<Task | null>(null)
  
  // 任务列表
  const tasks = ref<Task[]>([])
  
  // 当前任务的日志
  const logs = ref<LogEntry[]>([])
  const maxLogs = 1000 // 最多保留1000条日志
  
  // 当前任务的进度
  const progress = ref({
    current_round: 0,
    max_rounds: 30,
    status: 'pending' as 'thinking' | 'executing' | 'completed' | 'failed' | 'pending',
    percentage: 0,
    message: ''
  })
  
  // 当前任务的工具执行记录
  const toolExecutions = ref<ToolExecution[]>([])
  
  // 当前任务的漏洞
  const vulnerabilities = ref<Vulnerability[]>([])
  
  // 当前任务的FLAGS
  const flags = ref<string[]>([])
  
  // LLM思考内容
  const llmThoughts = ref<Array<{ thought: string; round: number; timestamp: string }>>([])
  
  // 🔥 LLM响应内容（完整的assistant消息）
  const llmResponses = ref<Array<{ content: string; round: number; timestamp: string; has_tool_calls: boolean }>>([])
  
  // 🔥🔥🔥 Meta监督内容
  const metaSupervisions = ref<Array<{ 
    content: string; 
    round: number; 
    timestamp: string;
    intervention_needed: boolean;
    intervention_type?: string;
    reason: string;
    guidance_message?: string;
  }>>([])
  
  // 🔥🔥🔥 Payload大师指导
  const payloadGuidances = ref<Array<{
    content: string;
    round: number;
    timestamp: string;
    vuln_type: string;
    payloads: string[];
    tested_payloads: string[];
    suggested_payloads: string[];
    evolution_note: string;
  }>>([])
  
  // 🔥🔥🔥 战略分析（Strategic Supervisor）
  const strategicAnalyses = ref<Array<{
    content: string;
    round: number;
    timestamp: string;
    plan: any;
    creative: any;
    meta: any;
  }>>([])
  
  // 🔥🔥🔥 对话消息（user/assistant/tool）- 按角色卡片显示
  const conversationMessages = ref<Array<{
    role: 'user' | 'assistant' | 'tool' | 'system';
    content: string;
    timestamp: string;
    round: number;
    tool_calls?: any[];
    has_tool_calls?: boolean;
    tool_call_id?: string;
    tool_name?: string;
  }>>([])
  
  // 人工干预状态
  const isPaused = ref(false)
  const pendingInstructions = ref<string[]>([])
  
  // 🔥 LocalStorage key
  const getStorageKey = (taskId: string) => `task_data_${taskId}`
  
  // 计算属性
  const isRunning = computed(() => currentTask.value?.status === 'running')
  const isCompleted = computed(() => currentTask.value?.status === 'completed')
  const isFailed = computed(() => currentTask.value?.status === 'failed')
  
  const criticalVulns = computed(() => 
    vulnerabilities.value.filter(v => v.severity === 'CRITICAL')
  )
  const highVulns = computed(() => 
    vulnerabilities.value.filter(v => v.severity === 'HIGH')
  )
  
  // 最近的日志(用于显示)
  const recentLogs = computed(() => logs.value.slice(-100))
  
  /**
   * 🔥 保存到LocalStorage
   */
  function saveToStorage(taskId: string) {
    try {
      const data = {
        logs: logs.value,
        toolExecutions: toolExecutions.value,
        vulnerabilities: vulnerabilities.value,
        flags: flags.value,
        llmThoughts: llmThoughts.value,
        progress: progress.value,
        savedAt: new Date().toISOString()
      }
      localStorage.setItem(getStorageKey(taskId), JSON.stringify(data))
    } catch (error) {
      console.error('保存任务数据失败:', error)
    }
  }
  
  /**
   * 🔥 从后端API加载历史消息（使用messages API）
   */
  async function loadMessagesFromAPI(taskId: string): Promise<boolean> {
    try {
      // 🔥 使用 messages API 获取所有历史消息
      const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}/messages?limit=1000`)
      if (!response.ok) return false
      
      const messages = await response.json()
      
      // 清空现有数据
      logs.value = []
      llmThoughts.value = []
      llmResponses.value = []
      toolExecutions.value = []
      vulnerabilities.value = []
      flags.value = []
      metaSupervisions.value = []
      payloadGuidances.value = []
      strategicAnalyses.value = []
      conversationMessages.value = []  // 🔥🔥🔥 添加清空
      
      // 🔥 根据消息类型分类处理
      for (const msg of messages) {
        switch (msg.type) {
          case 'log':
            logs.value.push({
              log_type: msg.metadata?.log_type || 'info',
              content: msg.content,
              timestamp: msg.created_at,
              metadata: msg.metadata || {}
            })
            break
            
          case 'llm_thinking':
            llmThoughts.value.push({
              thought: msg.content,
              round: msg.metadata?.round || msg.round || 0,  // 🔥 先从metadata读取
              timestamp: msg.created_at
            })
            break
            
          case 'llm_response':
            llmResponses.value.push({
              content: msg.content,
              round: msg.metadata?.round || msg.round || 0,  // 🔥 先从metadata读取
              timestamp: msg.created_at,
              has_tool_calls: msg.metadata?.has_tool_calls || false
            })
            break
            
          case 'tool_execution':
            toolExecutions.value.push({
              tool_name: msg.metadata?.tool_name || 'unknown',
              arguments: msg.metadata?.arguments || {},
              result: msg.content,
              execution_time: msg.metadata?.execution_time,
              timestamp: msg.created_at
            })
            break
            
          case 'vulnerability_found':
            if (msg.metadata?.vulnerability) {
              addVulnerability(msg.metadata.vulnerability)
            }
            break
            
          case 'flag_found':
            if (msg.metadata?.flag) {
              addFlag(msg.metadata.flag)
            }
            break
            
          case 'progress':
            // 更新进度
            if (msg.metadata) {
              progress.value = {
                current_round: msg.metadata.current_round || 0,
                max_rounds: msg.metadata.max_rounds || 0,
                status: msg.metadata.status || 'pending',
                percentage: msg.metadata.percentage || 0,
                message: msg.content
              }
            }
            break
            
          case 'conversation_message':
            // 🔥🔥🔥 处理对话消息
            conversationMessages.value.push({
              role: msg.metadata?.role || 'unknown',
              content: msg.content,
              timestamp: msg.created_at || msg.timestamp,  // 🔥 先从created_at读取
              round: msg.metadata?.round || msg.round || 0,  // 🔥 先从metadata读取
              tool_calls: msg.metadata?.tool_calls || null,
              has_tool_calls: msg.metadata?.has_tool_calls || false,
              tool_call_id: msg.metadata?.tool_call_id || null,
              tool_name: msg.metadata?.tool_name || null
            })
            break
        }
      }
      
      console.log(`✅ 从后端加载任务消息: ${taskId}`, {
        total: messages.length,
        logs: logs.value.length,
        thoughts: llmThoughts.value.length,
        responses: llmResponses.value.length,
        tools: toolExecutions.value.length,
        vulnerabilities: vulnerabilities.value.length,
        flags: flags.value.length,
        conversationMessages: conversationMessages.value.length  // 🔥🔥🔥 添加conversation统计
      })
      
      return true
    } catch (error) {
      console.error('加载任务消息失败:', error)
      return false
    }
  }
  
  /**
   * 🔥 清理旧数据（保留30天）
   */
  function cleanupOldStorage() {
    try {
      const keys = Object.keys(localStorage)
      const taskKeys = keys.filter(k => k.startsWith('task_data_'))
      
      taskKeys.forEach(key => {
        const data = JSON.parse(localStorage.getItem(key) || '{}')
        if (data.savedAt) {
          const savedDate = new Date(data.savedAt)
          const daysDiff = (Date.now() - savedDate.getTime()) / (1000 * 60 * 60 * 24)
          if (daysDiff > 30) {
            localStorage.removeItem(key)
            console.log(`🧹 清理超过30天的数据: ${key}`)
          }
        }
      })
    } catch (error) {
      console.error('清理旧数据失败:', error)
    }
  }
  
  /**
   * 设置当前任务
   */
  async function setCurrentTask(task: Task) {
    currentTask.value = task

    // 🔥 从后端API加载历史消息
    const loaded = await loadMessagesFromAPI(task.id)

    if (!loaded) {
      // 重置状态
      logs.value = []
      toolExecutions.value = []
      vulnerabilities.value = []
      flags.value = []
      llmThoughts.value = []
      progress.value = {
        current_round: 0,
        max_rounds: task.max_rounds,
        status: 'pending',
        percentage: 0,
        message: ''
      }
    }

    // 🔥 加载完成后立即清理无意义消息
    cleanupMeaninglessMessages()

    // 🔥 清理旧的LocalStorage数据
    cleanupOldStorage()
  }

  /**
   * 🔥 清理无意义的状态消息
   */
  function cleanupMeaninglessMessages() {
    // 清理Meta监督中的无意义消息
    metaSupervisions.value = metaSupervisions.value.filter(meta =>
      meta.content !== '✅ 状态： Worker运行正常，无需干预'
    )

    // 清理Payload大师中的无意义消息
    payloadGuidances.value = payloadGuidances.value.filter(payload =>
      payload.content !== '📊 状态： 当前无需提供payload建议'
    )

    console.log('🧹 清理完成，移除无意义状态消息')
  }
  
  /**
   * 处理WebSocket消息
   */
  function handleWebSocketMessage(message: WebSocketMessage) {
    switch (message.type) {
      case 'log':
        addLog(message as LogMessage)
        break
      
      case 'progress':
        updateProgress(message as ProgressMessage)
        break
      
      case 'tool_execution':
        addToolExecution(message as ToolExecutionMessage)
        break
      
      case 'llm_thinking':
        addLLMThought(message.thought, message.round, message.timestamp)
        break
      
      // 🔥 处理LLM响应
      case 'llm_response':
        addLLMResponse(message.content, message.round, message.timestamp, message.has_tool_calls)
        break
      
      // 🔥🔥🔥 处理Meta监督
      case 'meta_supervision':
        addMetaSupervision(message)
        break
      
      // 🔥🔥🔥 处理Payload大师指导
      case 'payload_guidance':
        addPayloadGuidance(message)
        break
      
      // 🔥🔥🔥 处理战略分析
      case 'strategic_analysis':
        addStrategicAnalysis(message)
        break
      
      // 🔥🔥🔥 处理对话消息（user/assistant/tool）
      case 'conversation_message':
        addConversationMessage(message)
        break
      
      case 'vulnerability_found':
        addVulnerability((message as VulnerabilityMessage).vulnerability)
        break
      
      case 'flag_found':
        addFlag((message as FlagMessage).flag)
        break
      
      case 'task_status':
        updateTaskStatus(message.status, message.data)
        break
      
      case 'intervention':
        handleIntervention(message.action, message.instruction)
        break
    }
    
    // 🔥🔥🔥 不再保存到LocalStorage（数据太大会爆）
    // 刷新页面时从后端API加载历史消息
    // if (currentTask.value) {
    //   saveToStorage(currentTask.value.id)
    // }
  }
  
  /**
   * 添加日志
   */
  function addLog(log: LogMessage) {
    // 🔥 去重：检查相同时间戳和内容
    const exists = logs.value.some(l => 
      l.timestamp === log.timestamp && 
      l.content === log.content
    )
    
    if (exists) return
    
    logs.value.push({
      log_type: log.log_type,
      content: log.content,
      timestamp: log.timestamp,
      metadata: log.metadata
    })
    
    // 限制日志数量
    if (logs.value.length > maxLogs) {
      logs.value = logs.value.slice(-maxLogs)
    }
  }
  
  /**
   * 更新进度
   */
  function updateProgress(prog: ProgressMessage) {
    progress.value = {
      current_round: prog.current_round,
      max_rounds: prog.max_rounds,
      status: prog.status,
      percentage: prog.percentage,
      message: prog.message || ''
    }
    
    // 同步到当前任务
    if (currentTask.value) {
      currentTask.value.current_round = prog.current_round
    }
  }
  
  /**
   * 添加工具执行记录
   */
  function addToolExecution(execution: ToolExecutionMessage) {
    // 🔥 去重：检查相同时间戳和工具名
    const exists = toolExecutions.value.some(t => 
      t.timestamp === execution.timestamp && 
      t.tool_name === execution.tool_name
    )
    
    if (exists) return
    
    toolExecutions.value.push({
      tool_name: execution.tool_name,
      arguments: execution.arguments,
      result: execution.result,
      execution_time: execution.execution_time,
      timestamp: execution.timestamp
    })
  }
  
  /**
   * 添加LLM思考
   */
  function addLLMThought(thought: string, round: number, timestamp: string) {
    // 🔥 去重：检查相同时间戳和轮次
    const exists = llmThoughts.value.some(t => 
      t.timestamp === timestamp && 
      t.round === round
    )
    
    if (exists) return
    
    llmThoughts.value.push({ thought, round, timestamp })
  }
  
  /**
   * 🔥 添加LLM响应（完整的assistant消息）
   */
  function addLLMResponse(content: string, round: number, timestamp: string, has_tool_calls: boolean = false) {
    // 去重：检查相同时间戳
    const exists = llmResponses.value.some(r => r.timestamp === timestamp)
    if (exists) return
    
    llmResponses.value.push({
      content,
      round,
      timestamp,
      has_tool_calls
    })
  }
  
  /**
   * 🔥🔥🔥 添加Meta监督
   */
  function addMetaSupervision(message: any) {
    // 🔥 过滤无意义的状态消息
    if (message.content === '✅ 状态： Worker运行正常，无需干预') {
      console.log('🚫 忽略无意义的Meta监督状态消息')
      return
    }

    // 🔥 更严格的去重：使用timestamp+round+content组合
    const exists = metaSupervisions.value.some(m => {
      // 如果有id，直接比较id
      if (message.id && m.id) {
        return m.id === message.id
      }
      // 否则比较timestamp+round+前50个字符内容（更精确）
      return m.timestamp === message.timestamp &&
             m.round === message.round &&
             m.content?.substring(0, 50) === message.content?.substring(0, 50)
    })
    if (exists) {
      console.log('🚫 忽略重复Meta监督:', message.round, message.content?.substring(0, 30))
      return
    }

    metaSupervisions.value.push({
      id: message.id,  // 🔥 保存id
      content: message.content,
      round: message.round,
      timestamp: message.timestamp || new Date().toISOString(),
      intervention_needed: message.intervention_needed || false,
      intervention_type: message.intervention_type,
      reason: message.reason || '',
      guidance_message: message.guidance_message
    })

    console.log('🔥 添加Meta监督:', message)
  }
  
  /**
   * 🔥🔥🔥 添加Payload大师指导
   */
  function addPayloadGuidance(message: any) {
    // 🔥 过滤无意义的状态消息
    if (message.content === '📊 状态： 当前无需提供payload建议') {
      console.log('🚫 忽略无意义的Payload大师状态消息')
      return
    }

    // 🔥 更严格的去重：使用timestamp+round+content组合
    const exists = payloadGuidances.value.some(p => {
      // 如果有id，直接比较id
      if (message.id && p.id) {
        return p.id === message.id
      }
      // 否则比较timestamp+round+前50个字符内容（更精确）
      return p.timestamp === message.timestamp &&
             p.round === message.round &&
             p.content?.substring(0, 50) === message.content?.substring(0, 50)
    })
    if (exists) {
      console.log('🚫 忽略重复Payload大师:', message.round, message.content?.substring(0, 30))
      return
    }

    payloadGuidances.value.push({
      id: message.id,  // 🔥 保存id
      content: message.content,
      round: message.round,
      timestamp: message.timestamp || new Date().toISOString(),
      vuln_type: message.vuln_type || 'unknown',
      payloads: message.payloads || [],
      tested_payloads: message.tested_payloads || [],
      suggested_payloads: message.suggested_payloads || [],
      evolution_note: message.evolution_note || ''
    })

    console.log('🔥 添加Payload大师指导:', message)
  }
  
  /**
   * 🔥🔥🔥 添加战略分析
   */
  function addStrategicAnalysis(message: any) {
    // 🔥 去重：使用timestamp+round+content组合
    const exists = strategicAnalyses.value.some((s: any) => {
      // 如果有id，直接比较id
      if (message.id && s.id) {
        return s.id === message.id
      }
      // 否则比较timestamp+round
      return s.timestamp === message.timestamp && s.round === message.round
    })
    if (exists) {
      console.log('🚫 忽略重复战略分析:', message.round)
      return
    }

    strategicAnalyses.value.push({
      id: message.id,
      content: message.content,
      round: message.round,
      timestamp: message.timestamp || new Date().toISOString(),
      plan: message.plan || {},
      creative: message.creative || {},
      meta: message.meta || {}
    })

    console.log('🔥 添加战略分析:', message)
  }
  
  /**
   * 🔥🔥🔥 添加对话消息（user/assistant/tool）
   */
  function addConversationMessage(message: any) {
    // 🔥 去重：使用timestamp+role+content前50字符
    const exists = conversationMessages.value.some((m: any) => {
      return m.timestamp === message.timestamp &&
             m.role === message.role &&
             m.content?.substring(0, 50) === message.content?.substring(0, 50)
    })
    if (exists) {
      console.log('🚫 忽略重复对话消息:', message.role, message.content?.substring(0, 30))
      return
    }
    
    conversationMessages.value.push({
      role: message.role,
      content: message.content || '',
      timestamp: message.timestamp || new Date().toISOString(),
      round: message.round || 0,
      tool_calls: message.tool_calls || null,
      has_tool_calls: message.has_tool_calls || false,
      tool_call_id: message.tool_call_id || null,
      tool_name: message.tool_name || null
    })
    
    console.log('🔥 添加对话消息:', message.role, message.content?.substring(0, 50))
  }
  
  /**
   * 添加漏洞
   */
  function addVulnerability(vuln: Omit<Vulnerability, 'discovered_at'>) {
    // 🔥 去重：检查相同类型、严重程度和描述
    const exists = vulnerabilities.value.some(v => 
      v.type === vuln.type && 
      v.severity === vuln.severity && 
      v.description === vuln.description
    )
    
    if (exists) {
      console.log('⚠️ 漏洞已存在，跳过:', vuln.type)
      return
    }
    
    vulnerabilities.value.push({
      ...vuln,
      discovered_at: new Date().toISOString()
    })
    
    console.log('✅ 添加漏洞:', vuln.type, vuln.severity)
  }
  
  /**
   * 添加FLAG
   */
  function addFlag(flag: string) {
    if (!flags.value.includes(flag)) {
      flags.value.push(flag)
    }
  }
  
  /**
   * 更新任务状态
   */
  function updateTaskStatus(status: string, data?: any) {
    if (currentTask.value) {
      currentTask.value.status = status as Task['status']
      
      if (status === 'completed') {
        currentTask.value.completed_at = new Date().toISOString()
      } else if (status === 'running' && !currentTask.value.started_at) {
        currentTask.value.started_at = new Date().toISOString()
      }
    }
  }
  
  /**
   * 处理人工干预
   */
  function handleIntervention(action: string, instruction?: string) {
    if (action === 'paused') {
      isPaused.value = true
    } else if (action === 'resumed') {
      isPaused.value = false
    } else if (action === 'instruction_injected' && instruction) {
      pendingInstructions.value.push(instruction)
    }
  }
  
  /**
   * 清空日志
   */
  function clearLogs() {
    logs.value = []
  }
  
  /**
   * 重置状态
   */
  function reset() {
    currentTask.value = null
    logs.value = []
    toolExecutions.value = []
    vulnerabilities.value = []
    flags.value = []
    llmThoughts.value = []
    llmResponses.value = []
    metaSupervisions.value = []  // 🔥🔥🔥 重置 Meta监督
    payloadGuidances.value = []  // 🔥🔥🔥 重置 Payload大师
    strategicAnalyses.value = []  // 🔥🔥🔥 重置战略分析
    progress.value = {
      current_round: 0,
      max_rounds: 30,
      status: 'pending',
      percentage: 0,
      message: ''
    }
    isPaused.value = false
    pendingInstructions.value = []
  }
  
  return {
    // State
    currentTask,
    tasks,
    logs,
    progress,
    toolExecutions,
    vulnerabilities,
    flags,
    llmThoughts,
    llmResponses,  // 🔥 添加导出
    metaSupervisions,  // 🔥🔥🔥 导出Meta监督
    payloadGuidances,  // 🔥🔥🔥 导出Payload大师
    strategicAnalyses,  // 🔥🔥🔥 导出战略分析
    conversationMessages,  // 🔥🔥🔥 导出对话消息
    isPaused,
    pendingInstructions,

    // Computed
    isRunning,
    isCompleted,
    isFailed,
    criticalVulns,
    highVulns,
    recentLogs,

    // Actions
    setCurrentTask,
    handleWebSocketMessage,
    addLog,
    updateProgress,
    addToolExecution,
    addLLMThought,
    addLLMResponse,  // 🔥 添加导出
    addVulnerability,
    addFlag,
    updateTaskStatus,
    clearLogs,
    reset,
    cleanupMeaninglessMessages  // 🔥 导出清理函数
  }
})
