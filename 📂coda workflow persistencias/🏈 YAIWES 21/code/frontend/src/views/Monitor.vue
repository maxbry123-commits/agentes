<template>
  <div class="monitor-page tech-background">
    <!-- 🔥 科技风背景层 -->
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    <div class="grid-overlay"></div>

    <!-- 顶部导航 -->
    <div class="top-bar">
      <el-button @click="$router.push('/')" class="glow-button">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2 class="tech-title">Task {{ taskId.slice(0, 8) }}</h2>
      <div class="actions">
        <el-button 
          v-if="store.currentTask?.status === 'completed' || store.currentTask?.status === 'failed'"
          type="primary"
          @click="showContinueDialog = true"
          class="glow-button"
        >
          <el-icon><RefreshRight /></el-icon>
          继续任务
        </el-button>
        
        <el-button 
          v-if="store.currentTask?.status === 'running' && !isPaused" 
          type="warning" 
          @click="pauseTask"
          class="glow-button"
        >
          <el-icon><VideoPause /></el-icon>
          暂停
        </el-button>
        
        <el-button 
          v-if="store.currentTask?.status === 'paused' || isPaused"
          type="success" 
          @click="resumeTask"
          class="glow-button"
        >
          <el-icon><VideoPlay /></el-icon>
          恢复
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="content">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <!-- 进度卡片 -->
        <el-card shadow="hover" class="progress-card tech-card">
          <template #header>
            <div class="card-header">
              <span class="tech-text">⚡ 执行进度</span>
              <el-tag :type="statusType">{{ statusText }}</el-tag>
            </div>
          </template>
          
          <div class="progress-content">
            <el-progress 
              :percentage="progress.percentage" 
              :status="progressStatus"
              :stroke-width="20"
            />
            <div class="progress-info">
              <span class="mono-text">Round {{ progress.current_round }} / {{ progress.max_rounds }}</span>
              <span class="tech-text-secondary">{{ progress.message }}</span>
            </div>
            <el-divider />
            <div class="stats">
              <div class="stat-item">
                <span class="label">🚩 发现FLAG:</span>
                <span class="value">{{ flags.length }}</span>
              </div>
              <div class="stat-item">
                <span class="label">🔥 发现漏洞:</span>
                <span class="value">{{ vulnerabilities.length }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 人工干预面板 -->
        <el-card shadow="hover" class="intervention-card tech-card">
          <template #header>
            <span class="tech-text">🎮 人工干预</span>
          </template>
          
          <el-input
            v-model="customInstruction"
            type="textarea"
            :rows="3"
            placeholder="输入自定义指令给Agent..."
          />
          <el-button 
            type="primary" 
            @click="injectInstruction" 
            :disabled="!customInstruction.trim()"
            style="margin-top: 10px; width: 100%;"
            class="glow-button"
          >
            <el-icon><Promotion /></el-icon>
            注入指令
          </el-button>
        </el-card>

        <!-- 上下文管理器面板 -->
        <el-card shadow="hover" class="context-card tech-card">
          <template #header>
            <span class="tech-text">🧠 上下文管理器</span>
            <el-tag v-if="contextStats.compression_events > 0" type="info" size="small" class="ml-2">
              已压缩 {{ contextStats.compression_events }} 次
            </el-tag>
          </template>
          
          <div class="context-content">
            <!-- Token 使用率 -->
            <div class="token-usage mb-3">
              <div class="d-flex justify-content-between align-center mb-1">
                <span class="tech-text-secondary">Token 使用率</span>
                <span class="mono-text small">{{ formatNumber(contextStats.current_tokens) }} / {{ formatNumber(contextStats.max_tokens) }}</span>
              </div>
              <el-progress 
                :percentage="tokenUsagePercentage" 
                :color="tokenUsageColor"
                :show-text="true"
                :format="formatTokenProgress"
              />
            </div>
            
            <!-- 压缩详情按钮 -->
            <el-button 
              v-if="contextStats.compression_events > 0"
              size="small" 
              type="primary" 
              plain
              @click="showCompressionDialog = true"
              class="w-100"
            >
              查看压缩详情
            </el-button>
          </div>
        </el-card>

        <!-- 🔥 任务计划面板（新增） -->
        <el-card v-if="taskPlan" shadow="hover" class="plan-card tech-card">
          <template #header>
            <span class="tech-text">📋 任务计划</span>
          </template>
          <TaskPlanViewer :plan="taskPlan" />
        </el-card>

  
        <!-- 漏洞列表 -->
        <el-card shadow="hover" class="vulns-card tech-card">
          <template #header>
            <span class="tech-text">⚠️ 发现的漏洞 ({{ vulnerabilities.length }})</span>
          </template>

          <div class="vulns-list">
            <div
              v-for="(vuln, index) in vulnerabilities"
              :key="index"
              class="vuln-item"
            >
              <el-tag
                :type="getSeverityType(vuln.severity)"
                size="small"
              >
                {{ vuln.severity }}
              </el-tag>
              <span class="vuln-type">{{ vuln.type }}</span>
            </div>
            <el-empty v-if="vulnerabilities.length === 0" description="暂无漏洞" />
          </div>
        </el-card>
      </div>

      <!-- 右侧面板 - 对话式展示 -->
      <div class="right-panel">
        <div class="chat-header">
          <h3>🤖 Agent对话记录</h3>
          <el-tag :type="statusType">{{ statusText }}</el-tag>
        </div>
        
        <div class="chat-container" ref="chatContainer">
          <!-- 消息列表 -->
          <div 
            v-for="(msg, index) in chatMessages" 
            :key="index"
            :class="['chat-message', msg.type]"
          >
            <!-- 系统消息 -->
            <div v-if="msg.type === 'system'" class="system-message">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ msg.content }}</span>
              <span class="time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            
            <!-- 🔥 LLM响应（新增） -->
            <div v-else-if="msg.type === 'llm_response' || msg.type === 'assistant'" class="llm-response-message">
              <div class="message-header">
                <el-avatar :size="36" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                  <el-icon><ChatDotRound /></el-icon>
                </el-avatar>
                <div class="sender-info">
                  <span class="sender-name">🤖 AI Agent</span>
                  <span class="time">{{ formatTime(msg.timestamp) }}</span>
                  <el-tag v-if="msg.round" size="small" type="info">Round {{ msg.round }}</el-tag>
                </div>
              </div>
              <div class="message-content llm-response">
                <div class="response-text">{{ msg.content }}</div>
                <div v-if="msg.has_tool_calls" class="tool-calling-indicator">
                  <el-icon><Tools /></el-icon>
                  <span>调用工具中...</span>
                </div>
              </div>
            </div>
            
            <!-- Agent思考 -->
            <div v-else-if="msg.type === 'thinking'" class="thinking-message">
              <div class="message-header">
                <el-avatar :size="32" style="background: #409eff">
                  <el-icon><ChatDotRound /></el-icon>
                </el-avatar>
                <div class="sender-info">
                  <span class="sender-name">💭 Agent思考</span>
                  <span class="time">{{ formatTime(msg.timestamp) }}</span>
                </div>
              </div>
              <div class="message-content thinking">
                <el-icon class="loading-icon"><Loading /></el-icon>
                <div class="thought-text">{{ msg.content }}</div>
              </div>
            </div>
            
            <!-- 🔥🔥🔥 Meta监督 -->
            <div v-else-if="msg.type === 'meta_supervision'" class="meta-supervision-message">
              <div class="message-header">
                <el-avatar :size="36" :style="msg.intervention_needed ? 'background: #f56c6c' : 'background: #409eff'">
                  <el-icon><View /></el-icon>
                </el-avatar>
                <div class="sender-info">
                  <span class="sender-name">👁️ Meta监督</span>
                  <span class="time">{{ formatTime(msg.timestamp) }}</span>
                  <el-tag size="small" type="info">Round {{ msg.round }}</el-tag>
                  <el-tag v-if="msg.intervention_needed" size="small" type="danger">需要干预</el-tag>
                </div>
              </div>
              <div class="message-content meta-supervision">
                <div v-if="msg.reason" class="meta-reason">
                  <strong>📝 分析：</strong> {{ msg.reason }}
                </div>
                <div v-else class="meta-reason">
                  <strong>✅ 状态：</strong> Worker运行正常，无需干预
                </div>
                <div v-if="msg.guidance_message" class="meta-guidance">
                  <strong>🎯 指导：</strong>
                  <pre>{{ msg.guidance_message }}</pre>
                </div>
                <el-tag v-if="msg.intervention_type" size="small" :type="msg.intervention_type === 'force_stop' ? 'danger' : 'warning'">
                  {{ msg.intervention_type }}
                </el-tag>
              </div>
            </div>
            
            <!-- 🔥🔥🔥 Payload大师指导 -->
            <div v-else-if="msg.type === 'payload_guidance'" class="payload-guidance-message">
              <div class="message-header">
                <el-avatar :size="36" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
                  <el-icon><MagicStick /></el-icon>
                </el-avatar>
                <div class="sender-info">
                  <span class="sender-name">🎯 Payload大师</span>
                  <span class="time">{{ formatTime(msg.timestamp) }}</span>
                  <el-tag size="small" type="info">Round {{ msg.round }}</el-tag>
                  <el-tag size="small" type="danger">{{ msg.vuln_type }}</el-tag>
                </div>
              </div>
              <div class="message-content payload-guidance">
                <div v-if="msg.evolution_note" class="payload-note">
                  <strong>💡 进化思路：</strong> {{ msg.evolution_note }}
                </div>
               
                <div v-if="msg.suggested_payloads && msg.suggested_payloads.length > 0" class="payload-list">
                  <strong>🚀 建议的Payload：</strong>
                  <ul>
                    <li v-for="(payload, idx) in msg.suggested_payloads.slice(0, 5)" :key="idx">
                      <code>{{ payload }}</code>
                    </li>
                  </ul>
                </div>
                <div v-if="msg.tested_payloads && msg.tested_payloads.length > 0" class="tested-info">
                  <el-tag size="small" type="info">已测试: {{ msg.tested_payloads.length }} 个</el-tag>
                </div>
              </div>
            </div>
            
            <!-- 工具调用 - 可折叠 -->
            <div v-else-if="msg.type === 'tool'" class="tool-message">
              <div class="message-header clickable" @click="toggleTool(index)">
                <el-avatar :size="32" style="background: #67c23a">
                  <el-icon><Tools /></el-icon>
                </el-avatar>
                <div class="sender-info">
                  <span class="sender-name">🔧 {{ msg.toolName }}</span>
                  <span class="time">{{ formatTime(msg.timestamp) }}</span>
                </div>
                <el-icon class="expand-icon" :class="{ expanded: expandedTools.has(index) }">
                  <ArrowRight />
                </el-icon>
              </div>
              <el-collapse-transition>
                <div v-show="expandedTools.has(index)" class="message-content tool">
                  <div class="tool-result">
                    <!-- 🔥 显示完整结果，添加滚动条 -->
                    <pre>{{ msg.content }}</pre>
                  </div>
                </div>
              </el-collapse-transition>
            </div>
            
            <!-- 成功消息（FLAG等） -->
            <div v-else-if="msg.type === 'success'" class="success-message">
              <div class="message-header">
                <el-avatar :size="32" style="background: #67c23a">
                  <el-icon><SuccessFilled /></el-icon>
                </el-avatar>
                <div class="sender-info">
                  <span class="sender-name">✅ 成功</span>
                  <span class="time">{{ formatTime(msg.timestamp) }}</span>
                </div>
              </div>
              <div class="message-content success">
                {{ msg.content }}
              </div>
            </div>
            
            <!-- 错误消息 -->
            <div v-else-if="msg.type === 'error'" class="error-message">
              <div class="message-header">
                <el-avatar :size="32" style="background: #f56c6c">
                  <el-icon><CircleCloseFilled /></el-icon>
                </el-avatar>
                <div class="sender-info">
                  <span class="sender-name">❌ 错误</span>
                  <span class="time">{{ formatTime(msg.timestamp) }}</span>
                </div>
              </div>
              <div class="message-content error">
                {{ msg.content }}
              </div>
            </div>
            
            <!-- Exploit attempts (新增) -->
            <div v-else-if="msg.type === 'exploit'" class="exploit-message">
              <div class="message-header">
                <el-avatar :size="32" :style="msg.success ? 'background: #67c23a' : 'background: #e6a23c'">
                  <el-icon><Lightning /></el-icon>
                </el-avatar>
                <div class="sender-info">
                  <span class="sender-name">💥 {{ msg.vulnerability || 'Payload大师' }}</span>
                  <span class="time">{{ formatTime(msg.timestamp) }}</span>
                </div>
                <el-tag :type="msg.success ? 'success' : 'warning'" size="small">
                  {{ msg.success ? '成功' : '尝试' }}
                </el-tag>
              </div>
              <div class="message-content exploit">
                <div v-if="msg.payload" class="exploit-detail">
                  <strong>Payload:</strong>
                  <pre>{{ msg.payload }}</pre>
                </div>
                <div v-if="msg.result" class="exploit-detail">
                  <strong>结果:</strong>
                  <pre>{{ msg.result }}</pre>
                </div>
                <div v-if="msg.metadata" class="exploit-metadata">
                  <el-tag v-for="(value, key) in msg.metadata" :key="key" size="small" style="margin: 2px;">
                    {{ key }}: {{ value }}
                  </el-tag>
                </div>
              </div>
            </div>
            
            <!-- 普通日志 -->
            <div v-else class="info-message">
              <div class="message-content info">
                <span class="time">{{ formatTime(msg.timestamp) }}</span>
                <span class="info-text">{{ msg.content }}</span>
              </div>
            </div>
          </div>
          
          <!-- 空状态 -->
          <el-empty v-if="chatMessages.length === 0" description="等待Agent开始工作..." />
        </div>
      </div>
    </div>
    
    <!-- 压缩详情对话框 -->
    <el-dialog
      v-model="showCompressionDialog"
      title="压缩可视化详情"
      width="80%"
      :destroy-on-close="true"
    >
      <div v-if="compressionDetails" class="compression-details">
        <!-- 压缩统计 -->
        <el-row :gutter="20" class="mb-4">
          <el-col :span="6">
            <el-statistic title="压缩前消息" :value="compressionDetails.total_messages" />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="压缩后消息" 
              :value="compressionDetails.current_messages"
              :value-style="{ color: '#3f8600' }"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="节省 Tokens" 
              :value="compressionDetails.tokens_saved"
              :value-style="{ color: '#F56C6C' }"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="压缩比" 
              :value="(compressionDetails.compression_ratio * 100).toFixed(1) + '%'"
              :value-style="{ color: '#409EFF' }"
            />
          </el-col>
        </el-row>
        
        <!-- 消息分析 -->
        <div v-if="compressionDetails.message_analysis" class="message-analysis">
          <h4>消息价值分析</h4>
          <el-table :data="compressionDetails.message_analysis.slice(0, 20)" stripe>
            <el-table-column prop="role" label="角色" width="80">
              <template #default="{ row }">
                <el-tag :type="getRoleType(row.role)" size="small">
                  {{ row.role }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content_preview" label="内容预览" show-overflow-tooltip />
            <el-table-column prop="token_count" label="Tokens" width="80" />
            <el-table-column prop="pentest_value" label="价值" width="100">
              <template #default="{ row }">
                <el-rate 
                  v-model="row.pentest_value" 
                  disabled 
                  show-score 
                  text-color="#ff9900"
                  score-template="{value}%"
                  :max="1"
                />
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80">
              <template #default="{ row }">
                <el-tag :type="getPriorityType(row.priority)" size="small">
                  {{ row.priority }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
    
    <!-- 🔥 继续任务对话框 -->
    <el-dialog 
      v-model="showContinueDialog" 
      title="继续任务" 
      width="500px"
    >
      <el-form label-width="120px">
        <el-form-item label="当前轮次">
          <el-text>{{ store.currentTask?.current_round }} / {{ store.currentTask?.max_rounds }}</el-text>
        </el-form-item>
        
        <el-form-item label="增加轮次">
          <el-input-number 
            v-model="additionalRounds" 
            :min="1" 
            :max="100" 
          />
        </el-form-item>
        
        <el-alert 
          type="info" 
          :closable="false"
          style="margin-top: 10px;"
        >
          将从当前轮次继续执行，保留所有历史对话
        </el-alert>
      </el-form>
      
      <template #footer>
        <el-button @click="showContinueDialog = false">取消</el-button>
        <el-button type="primary" @click="continueTask">开始继续</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/taskStore'
import { MessagePollingService } from '@/services/message-polling'
import { WebSocketService } from '@/services/websocket'
import type { TaskMessage } from '@/services/message-polling'
import TaskPlanViewer from '@/components/TaskPlanViewer.vue'
import axios from 'axios'

const route = useRoute()
const router = useRouter()  // 🔥 添加router
const taskId = computed(() => route.params.id as string)
const store = useTaskStore()

// 🔥 使用轮询服务替代WebSocket
const pollingService = ref<MessagePollingService | null>(null)

// 🔥 状态刷新定时器
const statusRefreshInterval = ref<number | null>(null)

// 上下文管理器定时器
const contextInterval = ref<NodeJS.Timeout | null>(null)

// 状态
const customInstruction = ref('')
const chatContainer = ref<HTMLElement>()
const expandedTools = ref<Set<number>>(new Set())
const taskPlan = ref<any>(null)  // 🔥 任务计划

// 🔥 继续任务对话框
const showContinueDialog = ref(false)
const additionalRounds = ref(10)

// 聊天消息（转换store中的数据为聊天格式）
const chatMessages = computed(() => {
  const messages: any[] = []
  
  // 🔥 添加系统消息（只添加一次）
  if (store.currentTask) {
    messages.push({
      type: 'system',
      content: `开始渗透测试: ${store.currentTask.target_url}`,
      timestamp: store.currentTask.created_at,
      _id: 'system_start'  // 🔥 独特ID防止重复
    })
  }
  
  // 添加日志消息
  store.logs.forEach(log => {
    // 🔥 过滤掉"[Round X] LLM思考完成"日志，避免与llm_thinking重复
    if (log.content.includes('LLM思考完成')) {
      return
    }

    // 🔥 处理exploit attempts，显示payload和metadata
    if (log.metadata && (log.metadata.vulnerability || log.metadata.payload)) {
      messages.push({
        type: 'exploit',
        content: log.content,
        timestamp: log.timestamp,
        metadata: log.metadata,
        vulnerability: log.metadata.vulnerability,
        payload: log.metadata.payload,
        result: log.metadata.result,
        success: log.metadata.success,
        _id: `exploit_${log.timestamp}`
      })
    } else if (log.log_type === 'success') {
      messages.push({
        type: 'success',
        content: log.content,
        timestamp: log.timestamp,
        _id: `success_${log.timestamp}`
      })
    } else if (log.log_type === 'error') {
      messages.push({
        type: 'error',
        content: log.content,
        timestamp: log.timestamp,
        _id: `error_${log.timestamp}`
      })
    } else {
      messages.push({
        type: 'info',
        content: log.content,
        timestamp: log.timestamp,
        _id: `info_${log.timestamp}`
      })
    }
  })
  
  // 🔥 添加LLM响应（新增）
  store.llmResponses?.forEach((resp: any) => {
    messages.push({
      type: 'llm_response',
      content: resp.content,
      timestamp: resp.timestamp,
      round: resp.round,
      has_tool_calls: resp.has_tool_calls,
      _id: `llm_resp_${resp.timestamp}_${resp.round}`
    })
  })

  // 🔥🔥🔥 添加Meta监督（只显示有实际内容的）
  store.metaSupervisions?.forEach((meta: any) => {
    // 只显示有reason或guidance的消息
    if (!meta.reason && !meta.guidance_message) {
      return
    }

    messages.push({
      type: 'meta_supervision',
      content: meta.content,
      timestamp: meta.timestamp,
      round: meta.round,
      intervention_needed: meta.intervention_needed,
      intervention_type: meta.intervention_type,
      reason: meta.reason,
      guidance_message: meta.guidance_message,
      _id: `meta_${meta.timestamp}_${meta.round}`
    })
  })

  // 🔥🔥🔥 添加Payload大师指导（只显示有实际内容的）
  store.payloadGuidances?.forEach((payload: any) => {
    // 只显示有evolution_note或suggested_payloads的消息
    if (!payload.evolution_note && !payload.suggested_payloads?.length) {
      return
    }

    messages.push({
      type: 'payload_guidance',
      content: payload.content,
      timestamp: payload.timestamp,
      round: payload.round,
      vuln_type: payload.vuln_type,
      payloads: payload.payloads,
      tested_payloads: payload.tested_payloads,
      suggested_payloads: payload.suggested_payloads,
      evolution_note: payload.evolution_note,
      _id: `payload_${payload.timestamp}_${payload.round}`
    })
  })
  
  // 🔥🔥🔥 添加对话消息（user/assistant/tool）
  console.log('💬 处理conversationMessages:', store.conversationMessages?.length || 0)
  store.conversationMessages?.forEach((conv: any, index: number) => {
    console.log(`  [${index}] role=${conv.role}, content=${conv.content?.substring(0, 30)}...`)
    
    if (conv.role === 'assistant') {
      messages.push({
        type: 'llm_response',
        content: conv.content,
        timestamp: conv.timestamp,
        round: conv.round,
        has_tool_calls: conv.has_tool_calls,
        _id: `conv_assistant_${conv.timestamp}`
      })
    } else if (conv.role === 'tool') {
      messages.push({
        type: 'tool',
        toolName: conv.tool_name || 'Unknown',
        content: conv.content,
        timestamp: conv.timestamp,
        _id: `conv_tool_${conv.timestamp}`
      })
    } else if (conv.role === 'user') {
      messages.push({
        type: 'system',
        content: conv.content,
        timestamp: conv.timestamp,
        _id: `conv_user_${conv.timestamp}`
      })
    }
  })
  
  // 🔥🔥🔥 调试日志
  console.log('💬 chatMessages computed:', {
    conversationMessagesCount: store.conversationMessages?.length || 0,
    totalMessages: messages.length,
    conversationMessages: store.conversationMessages
  })
  
  // 🔥🔥🔥 关键修复：只显示llmResponses，不显示llmThoughts，避免重复
  // store.llmThoughts.forEach(thought => {
  //   messages.push({
  //     type: 'thinking',
  //     content: thought.thought,
  //     timestamp: thought.timestamp,
  //     round: thought.round
  //   })
  // })
  
  // 🔥🔥🔥 注释掉toolExecutions，因为conversationMessages已经包含tool角色
  // store.toolExecutions.forEach(tool => {
  //   messages.push({
  //     type: 'tool',
  //     toolName: tool.tool_name,
  //     content: tool.result,
  //     timestamp: tool.timestamp,
  //     _id: `tool_${tool.tool_name}_${tool.timestamp}`
  //   })
  // })

  // 添加FLAG发现（使用独特ID避免重复）
  store.flags.forEach((flag, index) => {
    messages.push({
      type: 'success',
      content: `🚩 发现FLAG: ${flag}`,
      timestamp: new Date().toISOString(),
      _id: `flag_${index}_${flag}`,
      _sortTime: new Date().toISOString()  // 用于排序
    })
  })
  
  // 按时间排序并返回
  return messages.sort((a, b) => {
    const timeA = a._sortTime || a.timestamp
    const timeB = b._sortTime || b.timestamp
    return new Date(timeA).getTime() - new Date(timeB).getTime()
  })
})

// 从store获取数据
const logs = computed(() => store.recentLogs)
const progress = computed(() => store.progress)
const toolExecutions = computed(() => store.toolExecutions)
const llmThoughts = computed(() => store.llmThoughts)
const vulnerabilities = computed(() => {
  console.log('🐞 当前store.vulnerabilities:', store.vulnerabilities)
  console.log('🐞 store.vulnerabilities数量:', store.vulnerabilities.length)
  return store.vulnerabilities
})
const flags = computed(() => store.flags)
const isPaused = computed(() => store.isPaused)

// 上下文管理器数据
const contextStats = ref({
  current_messages: 0,
  current_tokens: 0,
  max_tokens: 120000,
  compression_events: 0,
  langchain_active: false,
  memory_type: 'buffer',
  attack_stage: 'recon',
  found_vectors: [],
  successful_attacks: 0,
  flags_found: []
})
const showCompressionDialog = ref(false)
const compressionDetails = ref(null)

// 上下文管理器计算属性
const tokenUsagePercentage = computed(() => {
  if (!contextStats.value.max_tokens) return 0
  return Math.round((contextStats.value.current_tokens / contextStats.value.max_tokens) * 100)
})

const tokenUsageColor = computed(() => {
  const pct = tokenUsagePercentage.value
  if (pct < 50) return '#67C23A'
  if (pct < 80) return '#E6A23C'
  return '#F56C6C'
})

const isRunning = computed(() => store.isRunning)
const statusText = computed(() => {
  const statusMap: any = {
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停',
    pending: '等待中'
  }
  return statusMap[store.currentTask?.status || 'pending'] || '未知'
})

const statusType = computed(() => {
  const typeMap: any = {
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    paused: 'warning',
    pending: 'info'
  }
  return typeMap[store.currentTask?.status || 'pending'] || 'info'
})

const progressStatus = computed(() => {
  if (progress.value.status === 'completed') return 'success'
  if (progress.value.status === 'failed') return 'exception'
  return undefined
})

// 方法
// 上下文管理器相关方法
const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const formatTokenProgress = (percentage) => {
  return `${percentage}% (${formatNumber(contextStats.value.current_tokens)} tokens)`
}

const fetchContextInfo = async () => {
  try {
    // 传递task_id参数
    const response = await axios.get('http://localhost:8000/api/v1/context/info', {
      params: {
        task_id: taskId.value
      }
    })
    contextStats.value = response.data
    console.log('[前端] Context stats updated:', response.data)
  } catch (error) {
    console.error('获取上下文信息失败:', error)
  }
}

const showCompressionDetails = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/v1/context/compression')
    compressionDetails.value = response.data
    showCompressionDialog.value = true
  } catch (error) {
    console.error('获取压缩详情失败:', error)
  }
}

const loadTask = async () => {
  try {
    const { data } = await axios.get(`http://localhost:8000/api/v1/tasks/${taskId.value}`)

    // 🔥 更新Store中的任务状态
    await store.setCurrentTask(data)

    // 🔥 调试：手动检查store中的数据
    console.log('🐞 store.vulnerabilities after setCurrentTask:', store.vulnerabilities)
    console.log('🐞 store.vulnerabilities.length:', store.vulnerabilities.length)

    // 🔥 在载载后强制更新一次状态，确保按钮显示正确
    if (data.status === 'running') {
      store.updateTaskStatus('running')
    } else if (data.status === 'paused') {
      store.updateTaskStatus('paused')
    } else if (data.status === 'completed') {
      store.updateTaskStatus('completed')
    } else if (data.status === 'failed') {
      store.updateTaskStatus('failed')
    }

    console.log('✅ 任务加载成功:', data.id, '状态:', data.status)
    return true
  } catch (error: any) {
    // 🔥 任务不存在，静默处理
    if (error.response?.status === 404) {
      console.warn('⚠️ 任务不存在或已删除')
      ElMessage.warning('任务不存在')
      // 返回任务列表
      setTimeout(() => {
        router.push('/tasks')
      }, 1500)
      return false
    }
    console.error('加载任务失败:', error)
    ElMessage.error('加载任务失败')
    return false
  }
}

const connectPolling = async () => {
  // 🔥 检查任务状态
  const pollingInterval = (store.currentTask?.status === 'completed' || store.currentTask?.status === 'failed') ? 10000 : 3000
  
  console.log(`🔄 开始轮询，间隔: ${pollingInterval}ms`)
  pollingService.value = new MessagePollingService(taskId.value, pollingInterval)
  
  // 🔥 定期刷新任务状态（每3秒，与消息轮询同步）
  statusRefreshInterval.value = window.setInterval(async () => {
    try {
      const { data } = await axios.get(`http://localhost:8000/api/v1/tasks/${taskId.value}`)
      if (data.status !== store.currentTask?.status) {
        console.log(`🔄 任务状态变化: ${store.currentTask?.status} → ${data.status}`)
        store.updateTaskStatus(data.status)
      }
    } catch (error) {
      // 忽略错误
    }
  }, 3000)  // 🔥 改为3秒，更快响应
  
  // 开始轮询
  await pollingService.value.start((messages: TaskMessage[]) => {
    // 处理新消息
    messages.forEach(msg => {
      // 🔥 根据消息类型转换为WebSocket格式
      let wsMessage: any = {
        type: msg.type,
        timestamp: msg.timestamp
      }
      
      // 根据类型特殊处理
      if (msg.type === 'llm_thinking') {
        // 🔥 LLM思考：content是thought，metadata里有round
        wsMessage.thought = msg.content
        wsMessage.round = msg.metadata?.round || 0
      } else if (msg.type === 'llm_response') {
        // 🔥 LLM响应（新增）
        wsMessage.content = msg.content
        wsMessage.round = msg.metadata?.round || 0
        wsMessage.has_tool_calls = msg.metadata?.has_tool_calls || false
      } else if (msg.type === 'log') {
        // 🔥 日志：metadata里有log_type
        wsMessage.log_type = msg.metadata?.log_type || 'info'
        wsMessage.content = msg.content
        wsMessage.metadata = msg.metadata || {}
      } else if (msg.type === 'tool_execution') {
        // 🔥 工具执行 - 支持两种格式（metadata里或已展开）
        wsMessage.tool_name = msg.metadata?.tool_name || msg.tool_name || 'unknown'
        wsMessage.arguments = msg.metadata?.arguments || msg.arguments || {}
        wsMessage.result = msg.content
        wsMessage.execution_time = msg.metadata?.execution_time || msg.execution_time
        wsMessage.timestamp = msg.timestamp  // 🔥 确保有timestamp
        
        console.log('🔧 收到工具执行:', wsMessage.tool_name, '时间:', wsMessage.timestamp)
      } else if (msg.type === 'progress') {
        // 🔥 进度更新
        wsMessage.current_round = msg.metadata?.current_round || 0
        wsMessage.max_rounds = msg.metadata?.max_rounds || 0
        wsMessage.status = msg.metadata?.status || ''
        wsMessage.percentage = msg.metadata?.percentage || 0
        wsMessage.message = msg.content
      } else if (msg.type === 'vulnerability_found') {
        // 🔥 漏洞发现
        // 🔥🔥🔥 后端存储在metadata.vulnerability中
        const vuln = msg.metadata?.vulnerability || msg.vulnerability || {
          type: msg.metadata?.type || 'Unknown',
          severity: msg.metadata?.severity || 'MEDIUM',
          description: msg.content,
          url: msg.metadata?.url || '',
          evidence: msg.metadata?.evidence
        }
        wsMessage.vulnerability = vuln
      } else if (msg.type === 'flag_found') {
        // 🔥 FLAG发现
        // 🔥🔥🔥 后端存储在metadata.flag中
        wsMessage.flag = msg.metadata?.flag || msg.flag || msg.content
        wsMessage.submit_result = msg.metadata?.submit_result || msg.submit_result
      } else if (msg.type === 'task_status') {
        // 🔥 任务状态
        wsMessage.status = msg.metadata?.status || ''
        wsMessage.message = msg.content
        wsMessage.data = msg.metadata?.data
      } else if (msg.type === 'task_plan') {
        // 🔥 任务计划（新增）
        const planData = msg.metadata?.plan || JSON.parse(msg.content || '{}')
        console.log('📋 收到任务计划:', planData)
        taskPlan.value = planData
        wsMessage = { ...wsMessage, plan: planData }
      } else if (msg.type === 'meta_supervision') {
        // 🔥🔥🔥 Meta监督（新增）- 直接展开metadata
        wsMessage = {
          type: msg.type,
          content: msg.content,
          timestamp: msg.timestamp,
          round: msg.metadata?.round || msg.round || 'unknown',
          intervention_needed: msg.metadata?.intervention_needed || msg.intervention_needed || false,
          intervention_type: msg.metadata?.intervention_type || msg.intervention_type,
          reason: msg.metadata?.reason || msg.reason || '',
          guidance_message: msg.metadata?.guidance_message || msg.guidance_message || ''
        }
        console.log('👁️ 收到Meta监督:', wsMessage)
      } else if (msg.type === 'payload_guidance') {
        // 🔥🔥🔥 Payload大师（新增）- 直接展开metadata
        wsMessage = {
          type: msg.type,
          content: msg.content,
          timestamp: msg.timestamp,
          round: msg.metadata?.round || msg.round || 'unknown',
          vuln_type: msg.metadata?.vuln_type || msg.vuln_type || 'unknown',
          payloads: msg.metadata?.payloads || msg.payloads || [],
          tested_payloads: msg.metadata?.tested_payloads || msg.tested_payloads || [],
          suggested_payloads: msg.metadata?.suggested_payloads || msg.suggested_payloads || [],
          evolution_note: msg.metadata?.evolution_note || msg.evolution_note || ''
        }
        console.log('💥 收到Payload大师:', wsMessage)
      } else if (msg.type === 'strategic_analysis') {
        // 🔥🔥🔥 战略分析（新增）- 直接展开metadata
        wsMessage = {
          type: msg.type,
          content: msg.content,
          timestamp: msg.timestamp,
          round: msg.metadata?.round || msg.round || 'unknown',
          plan: msg.metadata?.plan || msg.plan || {},
          creative: msg.metadata?.creative || msg.creative || {},
          meta: msg.metadata?.meta || msg.meta || {}
        }
        console.log('🧠 收到战略分析:', wsMessage)
      } else if (msg.type === 'conversation_message') {
        // 🔥🔥🔥 对话消息（user/assistant/tool）
        wsMessage = {
          type: msg.type,
          role: msg.metadata?.role || 'unknown',
          content: msg.content,
          timestamp: msg.timestamp,
          round: msg.metadata?.round || 0,
          tool_calls: msg.metadata?.tool_calls || null,
          has_tool_calls: msg.metadata?.has_tool_calls || false,
          tool_call_id: msg.metadata?.tool_call_id || null,
          tool_name: msg.metadata?.tool_name || null
        }
        console.log('💬 收到对话消息:', wsMessage.role, wsMessage.content?.substring(0, 50))
      } else {
        // 其他类型，直接展开metadata
        wsMessage = {
          type: msg.type,
          ...msg.metadata,
          content: msg.content,
          timestamp: msg.timestamp
        }
      }
      
      store.handleWebSocketMessage(wsMessage)
      
      // 🔥 检查是否任务完成
      if (msg.type === 'task_status' && (msg.metadata?.status === 'completed' || msg.metadata?.status === 'failed')) {
        console.log('✅ 任务已结束，减慢轮询')
        pollingService.value?.setPollingInterval(10000)
        ElMessage.success('任务已完成')
      }
    })
    
    // 🔥 移除自动滚动，让用户自己控制
    // nextTick(() => {
    //   if (chatContainer.value) {
    //     chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    //   }
    // })
  })
  
  ElMessage.success('已开始轮询任务消息')
}

const pauseTask = async () => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId.value}/intervention`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'pause' })
    })
    if (response.ok) {
      ElMessage.info('已发送暂停指令')
      // 🔥 立即刷新任务状态，不等10秒
      await loadTask()
    }
  } catch (error) {
    ElMessage.error('暂停失败')
  }
}

const resumeTask = async () => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId.value}/intervention`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'resume' })
    })
    if (response.ok) {
      ElMessage.info('已发送恢复指令')
      // 🔥 立即刷新任务状态，不等10秒
      await loadTask()
    }
  } catch (error) {
    ElMessage.error('恢复失败')
  }
}

const injectInstruction = async () => {
  if (!customInstruction.value.trim()) return
  
  try {
    const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId.value}/intervention`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        action: 'inject',
        instruction: customInstruction.value,
        priority: 'high'
      })
    })
    if (response.ok) {
      ElMessage.success(`已注入指令: ${customInstruction.value}`)
      customInstruction.value = ''
    }
  } catch (error) {
    ElMessage.error('指令注入失败')
  }
}

// 辅助方法
const getRoleType = (role) => {
  const types = {
    'user': 'primary',
    'assistant': 'success',
    'system': 'info',
    'tool': 'warning'
  }
  return types[role] || ''
}

const getPriorityType = (priority) => {
  const types = {
    'critical': 'danger',
    'high': 'warning',
    'medium': 'primary',
    'low': 'info'
  }
  return types[priority] || ''
}

// 工具折叠控制
const toggleTool = (index: number) => {
  if (expandedTools.value.has(index)) {
    expandedTools.value.delete(index)
  } else {
    expandedTools.value.add(index)
  }
}

// 删除formatToolResult方法，直接显示完整内容

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN')
}

const getSeverityType = (severity: string) => {
  const typeMap: any = {
    'CRITICAL': 'danger',
    'HIGH': 'warning',
    'MEDIUM': 'primary',
    'LOW': 'info'
  }
  return typeMap[severity] || 'info'
}

// 🔥 继续任务
const continueTask = async () => {
  try {
    const { data } = await axios.post(
      `http://localhost:8000/api/v1/tasks/${taskId.value}/continue`,
      null,
      { params: { additional_rounds: additionalRounds.value } }
    )
    
    ElMessage.success(`任务已继续，增加${additionalRounds.value}轮`)
    showContinueDialog.value = false
    
    // 重新加载任务
    await loadTask()
    
    // 切换到快速轮询
    if (pollingService.value) {
      pollingService.value.setPollingInterval(3000)
    }
  } catch (error: any) {
    console.error('继续任务失败:', error)
    ElMessage.error(error.response?.data?.detail || '继续任务失败')
  }
}

onMounted(async () => {
  console.log('🛠️ Monitor组件加载')

  // 🔥 立即清理store中的无意义消息
  store.cleanupMeaninglessMessages()

  const loaded = await loadTask()
  // 🔥 只有任务加载成功才启动轮询
  if (loaded) {
    await connectPolling()

    // 🔥 再次清理无意义消息
    store.cleanupMeaninglessMessages()
  }

  // 获取上下文信息
  await fetchContextInfo()

  // 定期更新上下文信息
  contextInterval.value = setInterval(() => {
    fetchContextInfo()
  }, 5000)
})

onUnmounted(() => {
  console.log('🧹 Monitor组件卸载，停止轮询')
  
  // 停止轮询
  if (pollingService.value) {
    pollingService.value.stop()
  }
  
  // 🔥 清理状态刷新定时器
  if (statusRefreshInterval.value) {
    clearInterval(statusRefreshInterval.value)
  }
  
  // 清理上下文定时器
  if (contextInterval.value) {
    clearInterval(contextInterval.value)
  }
  
  store.reset()
})
</script>

<style scoped>
/* 🔥 科技风 Monitor 页面 */
.monitor-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(64, 158, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 2;
}

.top-bar h2 {
  margin: 0;
  font-size: 20px;
  letter-spacing: 2px;
}

.actions {
  display: flex;
  gap: 10px;
}

.content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.left-panel {
  width: 350px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(64, 158, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-content {
  padding: 10px 0;
}

.progress-info {
  margin-top: 15px;
  display: flex;
  justify-content: space-between;
  color: #606266;
  font-size: 14px;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item .label {
  color: #909399;
  font-size: 14px;
}

.stat-item .value {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.vulns-list {
  max-height: 300px;
  overflow-y: auto;
}

.vuln-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-bottom: 1px solid #ebeef5;
}

.vuln-type {
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

/* 对话区域 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 2px solid rgba(64, 158, 255, 0.2);
  background: rgba(255, 255, 255, 0.02);
}

.chat-header h3 {
  margin: 0;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 1px;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-height: calc(100vh - 200px);
  min-height: 400px;
}

.chat-message {
  margin-bottom: 20px;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  
  &.clickable {
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      opacity: 0.8;
    }
  }
}

.sender-info {
  display: flex;
  flex-direction: column;
}

.sender-name {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
}

.message-content {
  margin-left: 42px;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-content.thinking {
  background: rgba(64, 158, 255, 0.1);
  border-left: 3px solid #409eff;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  
  .thought-text {
    flex: 1;
    white-space: pre-wrap;
    color: rgba(255, 255, 255, 0.9);
  }
}

/* 🔥 LLM响应样式 */
.message-content.llm-response {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.12) 100%);
  border-left: 3px solid #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);

  .response-text {
    white-space: pre-wrap;
    color: rgba(255, 255, 255, 0.98);
    line-height: 1.8;
    font-size: 14px;
    font-weight: 400;
  }

  .tool-calling-indicator {
    margin-top: 12px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: linear-gradient(135deg, rgba(103, 194, 58, 0.25) 0%, rgba(103, 194, 58, 0.15) 100%);
    border-radius: 6px;
    color: #95de64;
    font-size: 13px;
    font-weight: 500;
    border: 1px solid rgba(103, 194, 58, 0.3);
  }
}

.llm-response-message {
  margin-bottom: 20px;
  animation: slideInLeft 0.4s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.message-content.tool {
  background: rgba(103, 194, 58, 0.05);
  border-left: 3px solid #67c23a;
  max-height: 650px;
  overflow-y: auto;
}

.message-content.success {
  background: rgba(103, 194, 58, 0.1);
  border-left: 3px solid #67c23a;
  color: #67c23a;
  font-weight: 600;
}

.message-content.error {
  background: rgba(245, 108, 108, 0.1);
  border-left: 3px solid #f56c6c;
  color: #f56c6c;
}

/* 🔥 Exploit attempts样式 */
.message-content.exploit {
  background: linear-gradient(135deg, rgba(230, 162, 60, 0.1) 0%, rgba(245, 166, 35, 0.1) 100%);
  border-left: 3px solid #e6a23c;
}

.exploit-detail {
  margin-bottom: 12px;
}

.exploit-detail strong {
  color: rgba(255, 255, 255, 0.9);
  display: block;
  margin-bottom: 4px;
  font-size: 13px;
}

.exploit-detail pre {
  margin: 0;
  padding: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.exploit-metadata {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(230, 162, 60, 0.2);
}

.message-content.info {
  background: rgba(255, 255, 255, 0.02);
  padding: 8px 12px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
  display: flex;
  gap: 10px;
  align-items: center;
  
  .info-text {
    flex: 1;
  }
}

.tool-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  max-height: 600px;
  overflow-y: auto;
  line-height: 1.6;
}

.system-message {
  text-align: center;
  padding: 8px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.expand-icon {
  margin-left: auto;
  transition: transform 0.3s;
  
  &.expanded {
    transform: rotate(90deg);
  }
}

.loading-icon {
  animation: rotate 1s linear infinite;
  flex-shrink: 0;
  color: #409eff;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.tools-container {
  height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 15px;
}

.tool-detail {
  padding: 10px;
}

.tool-section {
  margin-bottom: 15px;
}

.tool-section h4 {
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 5px;
}

.tool-section pre {
  background: rgba(255, 255, 255, 0.02);
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  max-height: 400px;
  overflow-y: auto;
  color: rgba(255, 255, 255, 0.8);
}

.thought-item {
  margin-bottom: 20px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 8px;
}

.thought-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.thought-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.thought-content {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  white-space: pre-wrap;
}

.flags-container {
  height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
/* 上下文管理器样式 */
.context-card {
  margin-bottom: 15px;
}

.context-content .mono-text {
  font-family: 'Courier New', monospace;
}

.context-content .label {
  color: #909399;
  font-size: 12px;
}

.context-content .value {
  color: #409EFF;
  font-weight: bold;
}

.token-usage .el-progress-bar__outer {
  background-color: rgba(255, 255, 255, 0.1);
}

.attack-stages .el-steps--simple .el-step__title {
  font-size: 12px;
}

.discovery-stats .stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}

.discovery-stats .label {
  color: #909399;
  font-size: 12px;
}

.compression-details .el-statistic {
  text-align: center;
}

.compression-details .el-statistic .head {
  color: rgba(255, 255, 255, 0.7);
}

.compression-details .el-statistic .content {
  color: #fff;
}

.message-analysis {
  margin-top: 20px;
}

.message-analysis h4 {
  margin-bottom: 10px;
  color: #303133;
}

.w-100 {
  width: 100%;
}

/* 🔥🔥🔥 Meta监督样式 */
.meta-supervision-message {
  margin-bottom: 20px;
  animation: slideInLeft 0.4s ease-out;
}

.message-content.meta-supervision {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.12) 0%, rgba(64, 158, 255, 0.08) 100%);
  border-left: 4px solid #409eff;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.meta-reason {
  margin-bottom: 10px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.95);
  font-size: 14px;
}

.meta-reason strong {
  color: #409eff;
  font-weight: 600;
}

.meta-guidance {
  margin-top: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  border-left: 2px solid #e6a23c;
}

.meta-guidance pre {
  margin: 8px 0 0 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #67c23a;
  font-size: 13px;
  background: rgba(0, 0, 0, 0.2);
  padding: 8px;
  border-radius: 4px;
}

/* 🔥🔥🔥 Payload大师样式 */
.payload-guidance-message {
  margin-bottom: 20px;
  animation: slideInLeft 0.4s ease-out;
}

.message-content.payload-guidance {
  background: linear-gradient(135deg, rgba(240, 147, 251, 0.15) 0%, rgba(245, 87, 108, 0.12) 100%);
  border-left: 4px solid #f5576c;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(245, 87, 108, 0.2);
}

.payload-note {
  margin-bottom: 12px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.95);
  font-size: 14px;
}

.payload-note strong {
  color: #e6a23c;
  font-weight: 600;
}

.payload-list {
  margin-top: 12px;
}

.payload-list ul {
  margin: 8px 0;
  padding-left: 20px;
}

.payload-list li {
  margin: 6px 0;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.85);
}

.payload-list code {
  background: linear-gradient(135deg, rgba(103, 194, 58, 0.2) 0%, rgba(103, 194, 58, 0.1) 100%);
  padding: 6px 12px;
  border-radius: 6px;
  color: #95de64;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  word-break: break-all;
  border: 1px solid rgba(103, 194, 58, 0.3);
  display: inline-block;
  margin: 4px 0;
}

.tested-info {
  margin-top: 10px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
}

/* 📋 报告卡片样式 */
.report-card {
  margin-bottom: 15px;
}

.report-content {
  max-height: 600px;
  overflow-y: auto;
}

.report-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
}

.report-section:last-child {
  border-bottom: none;
}

.report-section h4 {
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 10px;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-text {
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
  font-size: 14px;
  margin: 0;
}

.vuln-report-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.vuln-report-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 15px;
  border-left: 3px solid #e6a23c;
}

.vuln-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.vuln-name {
  color: rgba(255, 255, 255, 0.95);
  font-weight: 600;
  font-size: 14px;
}

.cvss-score {
  background: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.vuln-desc {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  margin: 0 0 10px 0;
  font-size: 13px;
}

.timeline-time {
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
}

.recommendations-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.recommendations-list li {
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
  margin-bottom: 8px;
  padding-left: 20px;
  position: relative;
}

.recommendations-list li:before {
  content: "•";
  color: #67c23a;
  position: absolute;
  left: 8px;
}

/* 时间轴样式 */
.el-timeline {
  padding-left: 0;
}

.el-timeline-item__tail {
  border-left: 2px solid rgba(64, 158, 255, 0.3);
}

.el-timeline-item__node {
  background-color: #409eff;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.el-timeline-item__wrapper {
  padding-bottom: 10px;
}

.el-timeline-item__timestamp {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
}

</style>
