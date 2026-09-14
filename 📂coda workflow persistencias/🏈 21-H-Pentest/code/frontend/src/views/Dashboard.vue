<template>
  <div class="dashboard">
    <!-- 🔥 科技风背景层 -->
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    <div class="grid-overlay"></div>

    <el-container>
      <!-- 头部 -->
      <el-header height="60px" class="header">
        <div class="header-content">
          <div class="header-left">
            <h1>🔐 H-Pentest 渗透测试平台</h1>
            <div class="realtime-badge">
              <span class="pulse-dot"></span>
              <span>实时监控</span>
            </div>
          </div>
          <div class="header-right">
            <el-button @click="$router.push('/tasks')" text>
              <el-icon><List /></el-icon>
              任务管理
            </el-button>
            <el-button @click="$router.push('/settings')" text>
              <el-icon><Setting /></el-icon>
              系统配置
            </el-button>
            <el-button type="primary" @click="showCreateDialog = true" class="glow-button">
              <el-icon><Plus /></el-icon>
              新建任务
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main>
        <!-- 🔥 顶部核心指标 - 大数字展示 -->
        <el-row :gutter="20" class="stats-row">
          <el-col :span="4">
            <el-card shadow="hover" class="stat-card total">
              <div class="stat-content">
                <el-icon class="stat-icon"><DataAnalysis /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ totalTasks }}</div>
                  <div class="stat-label">总任务数</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="4">
            <el-card shadow="hover" class="stat-card running">
              <div class="stat-content">
                <el-icon class="stat-icon"><VideoPlay /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ runningCount }}</div>
                  <div class="stat-label">正在运行</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="4">
            <el-card shadow="hover" class="stat-card completed">
              <div class="stat-content">
                <el-icon class="stat-icon"><CircleCheck /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ completedCount }}</div>
                  <div class="stat-label">已完成</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="4">
            <el-card shadow="hover" class="stat-card failed">
              <div class="stat-content">
                <el-icon class="stat-icon"><CircleClose /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ failedCount }}</div>
                  <div class="stat-label">失败任务</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="4">
            <el-card shadow="hover" class="stat-card vulns">
              <div class="stat-content">
                <el-icon class="stat-icon"><WarnTriangleFilled /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ totalVulns }}</div>
                  <div class="stat-label">发现漏洞</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="4">
            <el-card shadow="hover" class="stat-card flags">
              <div class="stat-content">
                <el-icon class="stat-icon"><Flag /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ totalFlags }}</div>
                  <div class="stat-label">获取FLAG</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 🔥 中部数据展示区 - 真实数据 -->
        <el-row :gutter="20" style="margin-top: 20px;">
          <!-- 左：运行中任务实时监控 -->
          <el-col :span="12">
            <div class="tech-card" style="min-height: 380px;">
              <div class="card-header">
                <h3 class="tech-text">⚡ 运行中任务</h3>
                <div class="realtime-badge" v-if="runningCount > 0">
                  <span class="pulse-dot"></span>
                  <span>{{ runningCount }} 个运行中</span>
                </div>
              </div>
              <div class="running-tasks-list">
                <div v-if="runningTasks.length === 0" class="empty-state">
                  <el-icon size="48" color="#606266"><Moon /></el-icon>
                  <p>暂无运行中任务</p>
                </div>
                <div v-else class="task-item" v-for="task in runningTasks" :key="task.id" @click="$router.push(`/monitor/${task.id}`)">
                  <div class="task-header">
                    <span class="mono-text">{{ task.id.slice(0, 8) }}</span>
                    <el-tag size="small" :type="task.mode === 'ctf' ? 'danger' : 'primary'">{{ task.mode.toUpperCase() }}</el-tag>
                  </div>
                  <div class="task-target">{{ task.target_url }}</div>
                  <el-progress :percentage="Math.round((task.current_round / task.max_rounds) * 100)" :stroke-width="8" />
                  <div class="task-meta">
                    <span>Round {{ task.current_round }}/{{ task.max_rounds }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-col>

          <!-- 右：漏洞分布（真实数据） -->
          <el-col :span="12">
            <div class="tech-card" style="min-height: 380px; padding: 20px 25px;">
              <div class="card-header" style="margin-bottom: 20px;">
                <h3 class="tech-text">🔥 漏洞分布分析</h3>
              </div>
              <div class="vuln-chart">
                <div v-if="totalVulns === 0" class="empty-state">
                  <el-icon size="48" color="#67c23a"><CircleCheck /></el-icon>
                  <p>暂未发现漏洞</p>
                </div>
                <div v-else>
                  <div class="chart-bar">
                    <div class="bar-label">CRITICAL</div>
                    <div class="bar-container">
                      <div class="bar-fill critical" :style="{width: `${realVulnDistribution.critical.percent}%`}">
                        <span class="bar-value">{{ realVulnDistribution.critical.count }}</span>
                      </div>
                    </div>
                    <div class="bar-percent">{{ realVulnDistribution.critical.percent }}%</div>
                  </div>
                  <div class="chart-bar">
                    <div class="bar-label">HIGH</div>
                    <div class="bar-container">
                      <div class="bar-fill high" :style="{width: `${realVulnDistribution.high.percent}%`}">
                        <span class="bar-value">{{ realVulnDistribution.high.count }}</span>
                      </div>
                    </div>
                    <div class="bar-percent">{{ realVulnDistribution.high.percent }}%</div>
                  </div>
                  <div class="chart-bar">
                    <div class="bar-label">MEDIUM</div>
                    <div class="bar-container">
                      <div class="bar-fill medium" :style="{width: `${realVulnDistribution.medium.percent}%`}">
                        <span class="bar-value">{{ realVulnDistribution.medium.count }}</span>
                      </div>
                    </div>
                    <div class="bar-percent">{{ realVulnDistribution.medium.percent }}%</div>
                  </div>
                  <div class="chart-bar">
                    <div class="bar-label">LOW</div>
                    <div class="bar-container">
                      <div class="bar-fill low" :style="{width: `${realVulnDistribution.low.percent}%`}">
                        <span class="bar-value">{{ realVulnDistribution.low.count }}</span>
                      </div>
                    </div>
                    <div class="bar-percent">{{ realVulnDistribution.low.percent }}%</div>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 最近任务 -->
        <el-card shadow="hover" class="recent-tasks">
          <template #header>
            <div class="card-header">
              <span>最近任务</span>
              <el-button text @click="$router.push('/tasks')">查看全部</el-button>
            </div>
          </template>

          <el-table :data="recentTasks" stripe>
            <el-table-column prop="id" label="任务ID" width="100">
              <template #default="{ row }">
                {{ row.id.slice(0, 8) }}
              </template>
            </el-table-column>
            <el-table-column prop="target_url" label="目标URL" />
            <el-table-column prop="mode" label="模式" width="100">
              <template #default="{ row }">
                <el-tag :type="row.mode === 'ctf' ? 'danger' : 'primary'">
                  {{ row.mode.toUpperCase() }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="200">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-progress 
                    :percentage="Math.round((row.current_round / row.max_rounds) * 100)" 
                    :status="row.status === 'completed' ? 'success' : (row.status === 'failed' ? 'exception' : undefined)"
                    style="flex: 1;"
                  />
                  <span style="font-size: 12px; color: #909399;">{{ row.current_round }} / {{ row.max_rounds }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250">
              <template #default="{ row }">
                <el-button-group>
                  <!-- 🔥 正在运行：显示监控 -->
                  <el-button 
                    v-if="row.status === 'running'" 
                    size="small" 
                    type="primary"
                    @click="$router.push(`/monitor/${row.id}`)"
                  >
                    <el-icon><Monitor /></el-icon>
                    监控
                  </el-button>
                  
                  <!-- 🔥 已完成：显示对话 + 报告 -->
                  <el-button 
                    v-if="row.status === 'completed' || row.status === 'failed'" 
                    size="small"
                    type="success"
                    @click="$router.push(`/monitor/${row.id}`)"
                  >
                    <el-icon><ChatDotRound /></el-icon>
                    对话
                  </el-button>
                  
                  <el-button 
                    v-if="row.status === 'completed'" 
                    size="small"
                    @click="viewReport(row.id)"
                  >
                    <el-icon><Document /></el-icon>
                    报告
                  </el-button>
                  
                  <!-- 🔥 暂停状态：显示对话 -->
                  <el-button 
                    v-if="row.status === 'paused'" 
                    size="small"
                    @click="$router.push(`/monitor/${row.id}`)"
                  >
                    <el-icon><ChatDotRound /></el-icon>
                    对话
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建渗透测试任务" width="600px">
      <el-form :model="taskForm" label-width="120px">
        <el-form-item label="目标URL" required>
          <el-input v-model="taskForm.target_url" placeholder="http://target.com" />
        </el-form-item>
        
        <el-form-item label="测试模式" required>
          <el-radio-group v-model="taskForm.mode">
            <el-radio label="ctf">CTF竞赛模式</el-radio>
            <el-radio label="realworld">真实渗透测试</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="最大轮数">
          <el-input-number v-model="taskForm.max_rounds" :min="1" :max="100" />
        </el-form-item>

        <!-- 自定义目标 -->
        <el-form-item label="自定义目标">
          <el-input 
            v-model="taskForm.custom_objective" 
            type="textarea"
            :rows="4"
            maxlength="1000"
            show-word-limit
            placeholder="输入自定义渗透测试目标（选填，1000字以内）&#10;例如：&#10;- 找到管理员后台并获取权限&#10;- 提取数据库中的所有用户信息&#10;- 获取服务器Shell访问&#10;- 找到文件上传漏洞并上传Webshell"
          />
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">
            🎯 此目标将被注入到 Agent 的 System Prompt，指导 AI 的攻击策略
          </div>
        </el-form-item>

        <!-- CTF模式配置 -->
        <template v-if="taskForm.mode === 'ctf'">
          <el-divider>CTF配置</el-divider>
          <el-form-item label="FLAG提交URL">
            <el-input v-model="taskForm.flag_submit_url" placeholder="http://api.com/submit" />
          </el-form-item>
          <el-form-item label="Token">
            <el-input v-model="taskForm.token" placeholder="Bearer xxx..." />
          </el-form-item>
        </template>
        
        <!-- RealWorld模式配置 -->
        <template v-if="taskForm.mode === 'realworld'">
          <el-divider>🥷 RealWorld配置</el-divider>
          
          <el-form-item label="隐蔽模式">
            <el-switch 
              v-model="taskForm.stealth" 
              active-text="开启" 
              inactive-text="关闭"
              :active-value="true"
              :inactive-value="false"
            />
            <el-tooltip content="启用流量伪装: User-Agent轮换、HTTP头伪装、Payload混淆、参数污染 (不影响性能)" placement="right">
              <el-icon style="margin-left: 8px; cursor: help;"><QuestionFilled /></el-icon>
            </el-tooltip>
          </el-form-item>
          
          <el-form-item label="隐蔽级别" v-if="taskForm.stealth">
            <el-select v-model="taskForm.stealth_profile" placeholder="选择混淆强度">
              <el-option label="🟢 Balanced - 平衡级 (推荐)" value="balanced">
                <span>🟢 Balanced</span>
                <span style="color: #909399; font-size: 12px; margin-left: 8px;">中等混淆，不影响性能</span>
              </el-option>
              <el-option label="🟠 Stealth - 高级" value="stealth">
                <span>🟠 Stealth</span>
                <span style="color: #909399; font-size: 12px; margin-left: 8px;">高强度混淆</span>
              </el-option>
              <el-option label="🔴 Paranoid - 最高级" value="paranoid">
                <span>🔴 Paranoid</span>
                <span style="color: #909399; font-size: 12px; margin-left: 8px;">最强混淆</span>
              </el-option>
              <el-option label="🟡 Aggressive - 低级" value="aggressive">
                <span>🟡 Aggressive</span>
                <span style="color: #909399; font-size: 12px; margin-left: 8px;">低混淆，快速</span>
              </el-option>
            </el-select>
            <div style="margin-top: 8px; font-size: 12px; color: #909399;">
              💡 混淆技术: User-Agent轮换 + HTTP头伪装 + Payload混淆 + 参数污染
            </div>
          </el-form-item>
          
          <el-form-item label="合规标准">
            <el-input v-model="taskForm.compliance" placeholder="OWASP" />
          </el-form-item>
        </template>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTask" :loading="creating">
          创建并启动
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Plus, Setting, List, QuestionFilled } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/taskStore'  // 🔥 导入Store

const router = useRouter()
const taskStore = useTaskStore()

const tasks = ref<any[]>([])
const showCreateDialog = ref(false)
const creating = ref(false)
const particleCanvas = ref<HTMLCanvasElement>()

// 🔥 真实统计数据
const taskStats = ref({
  vulnerabilities: 0,
  flags: 0,
  vulnsBySeverity: { critical: 0, high: 0, medium: 0, low: 0 }
})

const taskForm = ref({
  target_url: '',
  mode: 'ctf',
  max_rounds: 30,
  flag_submit_url: '',
  token: '',
  custom_objective: '',  // 🔥 自定义目标
  // RealWorld模式参数
  stealth: false,
  stealth_profile: 'balanced',
  compliance: 'OWASP'
})

// 🔥 真实数据计算属性
const runningTasks = computed(() => 
  tasks.value.filter(t => t.status === 'running')
)

const runningCount = computed(() => runningTasks.value.length)

const completedCount = computed(() => 
  tasks.value.filter(t => t.status === 'completed').length
)

const totalVulns = computed(() => taskStats.value.vulnerabilities)

const totalFlags = computed(() => taskStats.value.flags)

const failedCount = computed(() => 
  tasks.value.filter(t => t.status === 'failed').length
)

const totalTasks = computed(() => tasks.value.length)

const recentTasks = computed(() => 
  tasks.value.slice(0, 10)
)

// 🔥 真实漏洞分布数据
const realVulnDistribution = computed(() => {
  const stats = taskStats.value.vulnsBySeverity
  const total = totalVulns.value || 1
  
  return {
    critical: {
      count: stats.critical,
      percent: Math.round((stats.critical / total) * 100)
    },
    high: {
      count: stats.high,
      percent: Math.round((stats.high / total) * 100)
    },
    medium: {
      count: stats.medium,
      percent: Math.round((stats.medium / total) * 100)
    },
    low: {
      count: stats.low,
      percent: Math.round((stats.low / total) * 100)
    }
  }
})

// 方法
const loadTasks = async () => {
  try {
    const { data } = await axios.get('http://localhost:8000/api/v1/tasks/')
    tasks.value = data
    
    // 🔥 统计所有任务的漏洞和FLAG（从messages API）
    await loadStats()
  } catch (error) {
    console.error('加载任务失败:', error)
  }
}

// 🔥 加载统计数据 - 直接从任务数据中统计
const loadStats = async () => {
  let vulnCount = 0
  let flagCount = 0
  const vulnsBySeverity = { critical: 0, high: 0, medium: 0, low: 0 }
  
  const completedTasks = tasks.value.filter(t => t.status === 'completed')
  
  if (completedTasks.length === 0) {
    taskStats.value = { vulnerabilities: 0, flags: 0, vulnsBySeverity }
    return
  }
  
  // 🔥 直接从任务对象中获取统计数据
  for (const task of completedTasks) {
    // 统计FLAGS
    flagCount += (task.flags_found || task.flags || []).length
    
    // 统计漏洞
    const vulns = task.vulnerabilities || []
    vulnCount += vulns.length
    
    vulns.forEach((v: any) => {
      const severity = (v.severity || '').toLowerCase()
      if (severity === 'critical') vulnsBySeverity.critical++
      else if (severity === 'high') vulnsBySeverity.high++
      else if (severity === 'medium') vulnsBySeverity.medium++
      else if (severity === 'low') vulnsBySeverity.low++
    })
  }
  
  taskStats.value = {
    vulnerabilities: vulnCount,
    flags: flagCount,
    vulnsBySeverity
  }
}

// 注意：Dashboard不需要WebSocket连接
// 只通过定时刷新获取任务状态即可

const createTask = async () => {
  if (!taskForm.value.target_url) {
    ElMessage.warning('请输入目标URL')
    return
  }

  // 🔥 打印发送的数据
  console.log('\n' + '='.repeat(80))
  console.log('📤 创建任务请求')
  console.log('='.repeat(80))
  console.log('Target URL:', taskForm.value.target_url)
  console.log('Mode:', taskForm.value.mode)
  console.log('Max Rounds:', taskForm.value.max_rounds)
  console.log('Flag Submit URL:', taskForm.value.flag_submit_url)
  console.log('Token:', taskForm.value.token)
  console.log('\n完整请求体:', JSON.stringify(taskForm.value, null, 2))
  console.log('='.repeat(80) + '\n')

  creating.value = true
  try {
    const { data } = await axios.post('http://localhost:8000/api/v1/tasks/', taskForm.value)
    
    // 🔥 打印响应
    console.log('\n' + '='.repeat(80))
    console.log('✅ 任务创建响应')
    console.log('='.repeat(80))
    console.log('Task ID:', data.id)
    console.log('Mode:', data.mode)
    console.log('Status:', data.status)
    console.log('\n完整响应:', JSON.stringify(data, null, 2))
    console.log('='.repeat(80) + '\n')
    
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    
    // 跳转到监控页面
    router.push(`/monitor/${data.id}`)
  } catch (error: any) {
    console.error('❌ 创建任务失败:', error)
    ElMessage.error(error.response?.data?.detail || '创建任务失败')
  } finally {
    creating.value = false
  }
}

const getStatusType = (status: string) => {
  const map: any = {
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    paused: 'warning',
    pending: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: any = {
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停',
    pending: '等待中'
  }
  return map[status] || status
}

const viewReport = (taskId: string) => {
  router.push(`/report/${taskId}`)
}

onMounted(() => {
  loadTasks()
  const timer = setInterval(loadTasks, 10000)
  initParticles()
  
  // 🔥 组件卸载时清理
  onUnmounted(() => {
    clearInterval(timer)
    console.log('🧹 Dashboard轮询已停止')
  })
})

// 🔥 粒子背景动画
const initParticles = () => {
  const canvas = particleCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')!
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const particles: any[] = []
  const particleCount = 80

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      radius: Math.random() * 1.5,
      dx: (Math.random() - 0.5) * 0.3,
      dy: (Math.random() - 0.5) * 0.3,
      opacity: Math.random() * 0.5
    })
  }

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    particles.forEach(p => {
      p.x += p.dx
      p.y += p.dy

      if (p.x < 0 || p.x > canvas.width) p.dx *= -1
      if (p.y < 0 || p.y > canvas.height) p.dy *= -1

      ctx.beginPath()
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(64, 158, 255, ${p.opacity})`
      ctx.fill()
    })

    // 连线
    particles.forEach((p1, i) => {
      particles.slice(i + 1).forEach(p2 => {
        const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y)
        if (dist < 120) {
          ctx.beginPath()
          ctx.moveTo(p1.x, p1.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.strokeStyle = `rgba(64, 158, 255, ${0.1 * (1 - dist / 120)})`
          ctx.stroke()
        }
      })
    })

    requestAnimationFrame(animate)
  }

  animate()

  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  })
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
  position: relative;
  overflow: hidden;
}

/* 🔥 科技风背景 */
.particle-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.grid-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(64, 158, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  z-index: 0;
  pointer-events: none;
}

.header {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(64, 158, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  position: relative;
  z-index: 10;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-content h1 {
  font-size: 24px;
  background: linear-gradient(90deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  font-weight: 900;
  letter-spacing: 2px;
  text-shadow: 0 0 20px rgba(64, 158, 255, 0.5);
}

/* 🔥 实时监控标记 */
.realtime-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(103, 194, 58, 0.1);
  border: 1px solid rgba(103, 194, 58, 0.3);
  border-radius: 20px;
  font-size: 12px;
  color: #67c23a;
  font-weight: 600;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #67c23a;
  border-radius: 50%;
  animation: pulse 2s infinite;
  box-shadow: 0 0 10px #67c23a;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.3);
  }
}

.glow-button {
  box-shadow: 0 0 20px rgba(64, 158, 255, 0.5);
  transition: all 0.3s;
  border: none;
}

.glow-button:hover {
  box-shadow: 0 0 30px rgba(64, 158, 255, 0.8);
  transform: translateY(-2px);
}

/* 🔥 科技风统计卡片 */
.stat-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid rgba(64, 158, 255, 0.2);
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  overflow: hidden;
  position: relative;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  transition: width 0.3s;
}

.stat-card::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 0;
  height: 0;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.2) 0%, transparent 70%);
  border-radius: 50%;
  transition: all 0.5s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(64, 158, 255, 0.3);
  border-color: rgba(64, 158, 255, 0.5);
}

.stat-card:hover::after {
  width: 200%;
  height: 200%;
}

.stat-card.total::before {
  background: linear-gradient(180deg, #909399, #606266);
}

.stat-card.running::before {
  background: linear-gradient(180deg, #409eff, #0066cc);
}

.stat-card.completed::before {
  background: linear-gradient(180deg, #67c23a, #4a8f2a);
}

.stat-card.failed::before {
  background: linear-gradient(180deg, #f56c6c, #c0392b);
}

.stat-card.vulns::before {
  background: linear-gradient(180deg, #e6a23c, #d68910);
}

.stat-card.flags::before {
  background: linear-gradient(180deg, #f39c12, #e67e22);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px;
}

.stat-icon {
  font-size: 40px;
  opacity: 0.9;
  filter: drop-shadow(0 0 10px currentColor);
}

.stat-card.total .stat-icon {
  color: #909399;
}

.stat-card.running .stat-icon {
  color: #409eff;
  animation: pulse-icon 2s ease-in-out infinite;
}

.stat-card.completed .stat-icon {
  color: #67c23a;
}

.stat-card.failed .stat-icon {
  color: #f56c6c;
}

.stat-card.vulns .stat-icon {
  color: #e6a23c;
}

.stat-card.flags .stat-icon {
  color: #f39c12;
}

@keyframes pulse-icon {
  0%, 100% {
    opacity: 1;
    filter: drop-shadow(0 0 10px currentColor);
  }
  50% {
    opacity: 0.6;
    filter: drop-shadow(0 0 20px currentColor);
  }
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 900;
  color: #fff;
  line-height: 1;
  margin-bottom: 4px;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* 🔥 任务列表科技风 */
.recent-tasks {
  margin-top: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(64, 158, 255, 0.2);
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 1;
}

.recent-tasks :deep(.el-card__header) {
  background: rgba(64, 158, 255, 0.05);
  border-bottom: 1px solid rgba(64, 158, 255, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 1px;
}

/* 🔥 表格科技风 */
.recent-tasks :deep(.el-table) {
  background: transparent;
  color: #fff;
}

.recent-tasks :deep(.el-table th.el-table__cell) {
  background: rgba(64, 158, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  border-bottom: 2px solid rgba(64, 158, 255, 0.3);
}

.recent-tasks :deep(.el-table tr) {
  background: transparent;
}

.recent-tasks :deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
}

.recent-tasks :deep(.el-table__body tr:hover > td) {
  background: rgba(64, 158, 255, 0.05) !important;
}

.recent-tasks :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(255, 255, 255, 0.02);
}

.stats-row {
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
}

/* 🔥 运行中任务列表 */
.running-tasks-list {
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.task-item {
  padding: 15px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.task-item:hover {
  background: rgba(64, 158, 255, 0.05);
  border-color: rgba(64, 158, 255, 0.3);
  transform: translateX(5px);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-target {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 8px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.4);
}

.empty-state p {
  margin-top: 15px;
  font-size: 14px;
}

/* 保留原有卡片样式 */
.card-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid rgba(64, 158, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
}

/* 漏洞图表 */
.vuln-chart {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.chart-bar {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 12px;
}

.chart-bar:last-child {
  margin-bottom: 0;
}

.bar-label {
  width: 100px;
  font-size: 13px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 1px;
}

.bar-container {
  flex: 1;
  height: 30px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  overflow: hidden;
  position: relative;
}

.bar-fill {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 10px;
  transition: width 1s ease;
  position: relative;
}

.bar-fill.critical {
  background: linear-gradient(90deg, #f56c6c, #c0392b);
  box-shadow: 0 0 15px rgba(245, 108, 108, 0.5);
}

.bar-fill.high {
  background: linear-gradient(90deg, #e6a23c, #d68910);
  box-shadow: 0 0 15px rgba(230, 162, 60, 0.5);
}

.bar-fill.medium {
  background: linear-gradient(90deg, #409eff, #0066cc);
  box-shadow: 0 0 15px rgba(64, 158, 255, 0.5);
}

.bar-fill.low {
  background: linear-gradient(90deg, #67c23a, #4a8f2a);
  box-shadow: 0 0 15px rgba(103, 194, 58, 0.5);
}

.bar-value {
  color: #fff;
  font-size: 14px;
  font-weight: 900;
  text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
}

.bar-percent {
  width: 60px;
  text-align: right;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  font-family: 'Courier New', monospace;
}
</style>
