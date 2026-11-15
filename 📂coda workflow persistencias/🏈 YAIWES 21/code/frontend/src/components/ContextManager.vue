<template>
  <div class="context-manager">
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-memory</v-icon>
        上下文管理器
        <v-spacer></v-spacer>
        <v-chip
          :color="contextInfo.langchain_active ? 'success' : 'warning'"
          small
        >
          {{ contextInfo.langchain_active ? 'LangChain 激活' : '传统模式' }}
        </v-chip>
      </v-card-title>
      
      <v-card-text>
        <!-- 统计信息 -->
        <v-row class="mb-4">
          <v-col cols="6" sm="3">
            <v-card outlined>
              <v-card-text class="text-center">
                <div class="text-h4 primary--text">{{ contextInfo.current_messages }}</div>
                <div class="caption">当前消息数</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card outlined>
              <v-card-text class="text-center">
                <div class="text-h4 info--text">{{ formatNumber(contextInfo.current_tokens) }}</div>
                <div class="caption">当前 Tokens</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card outlined>
              <v-card-text class="text-center">
                <div class="text-h4 warning--text">{{ contextInfo.compression_events }}</div>
                <div class="caption">压缩次数</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card outlined>
              <v-card-text class="text-center">
                <div class="text-h4 success--text">{{ contextInfo.flags_found.length }}</div>
                <div class="caption">找到的 FLAG</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Token 使用进度条 -->
        <v-card outlined class="mb-4">
          <v-card-title class="text-subtitle-1">Token 使用情况</v-card-title>
          <v-card-text>
            <v-progress-linear
              :value="tokenUsagePercentage"
              :color="tokenUsageColor"
              height="25"
              rounded
            >
              <template v-slot:default="{ value }">
                <strong>{{ Math.round(value) }}%</strong>
              </template>
            </v-progress-linear>
            <div class="mt-2 d-flex justify-space-between">
              <span class="caption">
                {{ formatNumber(contextInfo.current_tokens) }} / {{ formatNumber(contextInfo.max_tokens) }} tokens
              </span>
              <span class="caption" :class="`${tokenUsageColor}--text`">
                {{ tokenUsageStatus }}
              </span>
            </div>
          </v-card-text>
        </v-card>

        <!-- 攻击阶段和发现 -->
        <v-row>
          <v-col cols="12" md="6">
            <v-card outlined>
              <v-card-title class="text-subtitle-1">攻击进度</v-card-title>
              <v-card-text>
                <v-stepper alt-labels flat>
                  <v-stepper-header>
                    <v-stepper-step
                      :complete="isStageComplete('recon')"
                      :color="isStageActive('recon') ? 'primary' : ''"
                      step="1"
                    >
                      侦察
                    </v-stepper-step>
                    <v-divider></v-divider>
                    <v-stepper-step
                      :complete="isStageComplete('scan')"
                      :color="isStageActive('scan') ? 'primary' : ''"
                      step="2"
                    >
                      扫描
                    </v-stepper-step>
                    <v-divider></v-divider>
                    <v-stepper-step
                      :complete="isStageComplete('exploit')"
                      :color="isStageActive('exploit') ? 'primary' : ''"
                      step="3"
                    >
                      利用
                    </v-stepper-step>
                    <v-divider></v-divider>
                    <v-stepper-step
                      :complete="isStageComplete('post_exploit')"
                      :color="isStageActive('post_exploit') ? 'primary' : ''"
                      step="4"
                    >
                      后渗透
                    </v-stepper-step>
                  </v-stepper-header>
                </v-stepper>
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="12" md="6">
            <v-card outlined>
              <v-card-title class="text-subtitle-1">发现概要</v-card-title>
              <v-card-text>
                <v-list dense>
                  <v-list-item>
                    <v-list-item-icon>
                      <v-icon color="warning">mdi-target-account</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>攻击向量</v-list-item-title>
                      <v-list-item-subtitle>
                        {{ contextInfo.found_vectors.length > 0 
                           ? contextInfo.found_vectors.join(', ') 
                           : '未发现' }}
                      </v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-icon>
                      <v-icon color="success">mdi-check-all</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>成功攻击</v-list-item-title>
                      <v-list-item-subtitle>{{ contextInfo.successful_attacks.length }} 个</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 压缩可视化对话框 -->
    <v-dialog v-model="showCompressionDialog" max-width="800px">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-compress</v-icon>
          压缩可视化
        </v-card-title>
        <v-card-text>
          <v-row class="mb-4">
            <v-col cols="6">
              <v-card outlined>
                <v-card-text class="text-center">
                  <div class="text-h3 error--text">{{ compressionData.before_count }}</div>
                  <div class="caption">压缩前消息</div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="6">
              <v-card outlined>
                <v-card-text class="text-center">
                  <div class="text-h3 success--text">{{ compressionData.after_count }}</div>
                  <div class="caption">压缩后消息</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
          
          <v-alert type="success" v-if="compressionData.compression_ratio < 0.5">
            压缩成功！保留了 {{ Math.round(compressionData.compression_ratio * 100) }}% 的消息
          </v-alert>
          
          <v-simple-table v-if="compressionData.messages_kept.length > 0">
            <template v-slot:default>
              <thead>
                <tr>
                  <th class="text-left">保留的消息</th>
                  <th class="text-left">角色</th>
                  <th class="text-left">价值评分</th>
                  <th class="text-left">Tokens</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="msg in compressionData.messages_kept.slice(0, 5)" :key="msg.timestamp">
                  <td>{{ msg.content_preview }}</td>
                  <td>
                    <v-chip :color="getRoleColor(msg.role)" x-small>
                      {{ msg.role }}
                    </v-chip>
                  </td>
                  <td>{{ (msg.pentest_value * 100).toFixed(0) }}%</td>
                  <td>{{ msg.token_count }}</td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import { Chart } from 'chart.js'

export default {
  name: 'ContextManager',
  data() {
    return {
      contextInfo: {
        total_messages: 0,
        current_messages: 0,
        compression_events: 0,
        tokens_saved: 0,
        current_tokens: 0,
        max_tokens: 120000,
        memory_type: 'combined',
        langchain_active: true,
        attack_stage: 'recon',
        found_vectors: [],
        successful_attacks: [],
        flags_found: []
      },
      compressionData: {
        before_count: 0,
        after_count: 0,
        compression_ratio: 1.0,
        messages_kept: [],
        messages_removed: []
      },
      showCompressionDialog: false,
      ws: null,
      chart: null
    }
  },
  computed: {
    tokenUsagePercentage() {
      return (this.contextInfo.current_tokens / this.contextInfo.max_tokens) * 100
    },
    tokenUsageColor() {
      const percentage = this.tokenUsagePercentage
      if (percentage < 50) return 'success'
      if (percentage < 80) return 'warning'
      return 'error'
    },
    tokenUsageStatus() {
      const percentage = this.tokenUsagePercentage
      if (percentage < 50) return '充足'
      if (percentage < 80) return '适中'
      return '接近上限'
    }
  },
  mounted() {
    this.fetchContextInfo()
    this.initWebSocket()
    this.initTokenChart()
    
    // 定期更新数据
    this.interval = setInterval(() => {
      this.fetchContextInfo()
    }, 5000)
  },
  beforeDestroy() {
    if (this.ws) {
      this.ws.close()
    }
    if (this.interval) {
      clearInterval(this.interval)
    }
  },
  methods: {
    async fetchContextInfo() {
      try {
        const response = await axios.get('/api/v1/context/info')
        this.contextInfo = response.data
      } catch (error) {
        console.error('获取上下文信息失败:', error)
      }
    },
    
    async showCompressionVisualization() {
      try {
        const response = await axios.get('/api/v1/context/compression')
        this.compressionData = response.data
        this.showCompressionDialog = true
      } catch (error) {
        console.error('获取压缩数据失败:', error)
      }
    },
    
    initWebSocket() {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/context`
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'context_update') {
          this.contextInfo = { ...this.contextInfo, ...data.data }
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
      this.ws.onclose = () => {
        // 5秒后重连
        setTimeout(() => {
          this.initWebSocket()
        }, 5000)
      }
    },
    
    initTokenChart() {
      // 获取图表数据
      axios.get('/api/v1/context/token-chart')
        .then(response => {
          const chartData = response.data
          
          const ctx = this.$refs.tokenChart?.getContext('2d')
          if (ctx) {
            this.chart = new Chart(ctx, {
              type: 'line',
              data: {
                labels: chartData.labels,
                datasets: [
                  {
                    label: '当前 Tokens',
                    data: chartData.datasets.current,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                  },
                  {
                    label: '累计 Tokens',
                    data: chartData.datasets.cumulative,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                  }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Tokens'
                    }
                  }
                }
              }
            })
          }
        })
        .catch(error => {
          console.error('获取图表数据失败:', error)
        })
    },
    
    formatNumber(num) {
      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K'
      }
      return num.toString()
    },
    
    getRoleColor(role) {
      const colors = {
        user: 'blue',
        assistant: 'green',
        system: 'grey',
        tool: 'orange'
      }
      return colors[role] || 'grey'
    },
    
    isStageActive(stage) {
      return this.contextInfo.attack_stage === stage
    },
    
    isStageComplete(stage) {
      const stages = ['recon', 'scan', 'exploit', 'post_exploit']
      const currentIndex = stages.indexOf(this.contextInfo.attack_stage)
      const stageIndex = stages.indexOf(stage)
      return stageIndex < currentIndex
    }
  }
}
</script>

<style scoped>
.context-manager {
  margin-bottom: 20px;
}
</style>