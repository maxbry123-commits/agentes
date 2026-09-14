<template>
  <div class="test-context pa-4">
    <h1>上下文管理器测试</h1>
    
    <ContextManager />
    
    <v-card class="mt-4">
      <v-card-title>测试控制</v-card-title>
      <v-card-text>
        <v-btn 
          color="primary" 
          @click="fetchData"
          class="mr-2"
        >
          刷新数据
        </v-btn>
        
        <v-btn 
          color="secondary" 
          @click="showCompression"
        >
          查看压缩可视化
        </v-btn>
        
        <v-btn 
          color="info" 
          @click="fetchMessages"
          class="ml-2"
        >
          获取消息列表
        </v-btn>
      </v-card-text>
    </v-card>
    
    <!-- 消息列表 -->
    <v-card class="mt-4" v-if="messages.length > 0">
      <v-card-title>最近消息</v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item v-for="msg in messages" :key="msg.timestamp">
            <v-list-item-content>
              <v-list-item-title>
                <v-chip :color="getRoleColor(msg.role)" x-small class="mr-2">
                  {{ msg.role }}
                </v-chip>
                {{ msg.content_preview }}
              </v-list-item-title>
              <v-list-item-subtitle>
                Tokens: {{ msg.token_count }} | 
                价值: {{ (msg.pentest_value * 100).toFixed(0) }}% |
                优先级: {{ msg.priority }}
              </v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
    
    <!-- Token 使用图表 -->
    <v-card class="mt-4">
      <v-card-title>Token 使用趋势</v-card-title>
      <v-card-text>
        <canvas ref="tokenChart" height="100"></canvas>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import axios from 'axios'
import ContextManager from '@/components/ContextManager.vue'
import { Chart } from 'chart.js'

export default {
  name: 'TestContext',
  components: {
    ContextManager
  },
  data() {
    return {
      messages: []
    }
  },
  mounted() {
    this.fetchData()
    this.fetchMessages()
    this.initChart()
  },
  methods: {
    async fetchData() {
      try {
        const response = await axios.get('/api/v1/context/info')
        console.log('Context info:', response.data)
      } catch (error) {
        console.error('获取数据失败:', error)
      }
    },
    
    async showCompression() {
      try {
        const response = await axios.get('/api/v1/context/compression')
        console.log('Compression data:', response.data)
      } catch (error) {
        console.error('获取压缩数据失败:', error)
      }
    },
    
    async fetchMessages() {
      try {
        const response = await axios.get('/api/v1/context/messages?limit=10')
        this.messages = response.data
        console.log('Messages:', response.data)
      } catch (error) {
        console.error('获取消息失败:', error)
      }
    },
    
    initChart() {
      axios.get('/api/v1/context/token-chart')
        .then(response => {
          const chartData = response.data
          
          const ctx = this.$refs.tokenChart?.getContext('2d')
          if (ctx) {
            new Chart(ctx, {
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
    
    getRoleColor(role) {
      const colors = {
        user: 'blue',
        assistant: 'green',
        system: 'grey',
        tool: 'orange'
      }
      return colors[role] || 'grey'
    }
  }
}
</script>