<template>
  <div class="report-page tech-background">
    <!-- 🔥 科技风背景层 -->
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    <div class="grid-overlay"></div>

    <div class="report-header">
      <el-button @click="$router.back()" class="glow-button">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1 class="tech-title">📄 渗透测试报告</h1>
      <el-button type="primary" @click="exportReport" class="glow-button">
        <el-icon><Download /></el-icon>
        导出报告
      </el-button>
    </div>

    <div v-if="loading" class="loading">
      <el-icon class="is-loading" :size="60"><Loading /></el-icon>
      <span class="tech-text">加载报告中...</span>
    </div>

    <div v-else-if="report" class="report-content">
      <!-- 摘要 -->
      <div class="summary-section">
        <h2 class="section-header">
          <span class="icon-badge">📊</span>
          <span class="header-text">执行摘要</span>
        </h2>
        <div class="summary-grid">
          <div class="summary-item">
            <div class="item-label">目标URL</div>
            <div class="item-value url-value">{{ report.target_url }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">测试模式</div>
            <div class="item-value">
              <span class="mode-badge" :class="report.mode === 'ctf' ? 'mode-ctf' : 'mode-real'">
                {{ report.mode === 'ctf' ? 'CTF 夺旗' : 'RealWorld' }}
              </span>
            </div>
          </div>
          <div class="summary-item">
            <div class="item-label">总轮数</div>
            <div class="item-value number-value">{{ report.summary?.total_rounds || 0 }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">成功轮数</div>
            <div class="item-value number-value">{{ report.summary?.successful_rounds || 0 }}</div>
          </div>
          <div class="summary-item highlight-item">
            <div class="item-label">发现FLAG</div>
            <div class="item-value number-value highlight-number">
              <span class="big-number">{{ report.summary?.flags_found || 0 }}</span>
              <span class="unit">个</span>
            </div>
          </div>
          <div class="summary-item highlight-item">
            <div class="item-label">发现漏洞</div>
            <div class="item-value number-value highlight-number">
              <span class="big-number">{{ report.summary?.vulnerabilities_found || 0 }}</span>
              <span class="unit">个</span>
            </div>
          </div>
          <div class="summary-item">
            <div class="item-label">状态</div>
            <div class="item-value">
              <span class="status-badge" :class="report.summary?.status === 'completed' ? 'status-success' : 'status-pending'">
                <span class="status-dot"></span>
                {{ statusText }}
              </span>
            </div>
          </div>
          <div class="summary-item">
            <div class="item-label">生成时间</div>
            <div class="item-value time-value">{{ formatTime(report.generated_at) }}</div>
          </div>
        </div>
      </div>

      <!-- FLAGS -->
      <div v-if="report.flags_found && report.flags_found.length > 0" class="flags-section">
        <h2 class="section-header">
          <span class="icon-badge">🚩</span>
          <span class="header-text">发现的 FLAGS</span>
          <span class="count-badge">{{ report.flags_found.length }}</span>
        </h2>
        <div class="flags-list">
          <div v-for="(flag, index) in report.flags_found" :key="index" class="flag-item">
            <div class="flag-index">#{{ index + 1 }}</div>
            <div class="flag-content">
              <div class="flag-icon">🏁</div>
              <div class="flag-text">{{ flag }}</div>
              <button class="copy-btn" @click="copyFlag(flag)">
                <span class="copy-icon">📋</span>
                复制
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 漏洞列表 -->
      <el-card v-if="report.vulnerabilities && report.vulnerabilities.length > 0" shadow="hover" class="vulns-card tech-card">
        <template #header>
          <h2 class="tech-text">⚠️ 发现的漏洞 ({{ report.vulnerabilities.length }})</h2>
        </template>
        
        <!-- 🔥 漏洞卡片式展示（参考图片） -->
        <div v-for="(vuln, index) in report.vulnerabilities" :key="index" class="vuln-detail-card">
          <div class="vuln-header">
            <el-tag :type="getSeverityType(vuln.severity)" class="severity-tag">{{ vuln.severity }}</el-tag>
            <h3 class="vuln-title">{{ vuln.type }}</h3>
          </div>
          
          <!-- CVSS评分 -->
          <div v-if="vuln.cvss_score" class="cvss-section">
            <div class="cvss-label">📋 CVSS评分</div>
            <div class="cvss-value">{{ vuln.cvss_score }}</div>
          </div>
          
          <!-- 漏洞描述 -->
          <div class="section">
            <div class="section-icon">📋</div>
            <div class="section-title">漏洞描述</div>
            <div class="section-content">{{ vuln.description }}</div>
          </div>
          
          <!-- 影响分析 -->
          <div v-if="vuln.impact" class="section">
            <div class="section-icon">⭐</div>
            <div class="section-title">影响分析</div>
            <div class="section-content">{{ vuln.impact }}</div>
          </div>
          
          <!-- 复现步骤 -->
          <div v-if="vuln.reproduction_steps && vuln.reproduction_steps.length > 0" class="section">
            <div class="section-icon">🛠️</div>
            <div class="section-title">复现步骤</div>
            <div class="reproduction-steps">
              <div v-for="(step, stepIndex) in vuln.reproduction_steps" :key="stepIndex" class="repro-step">
                <div class="step-number">{{ stepIndex + 1 }}</div>
                <div class="step-content">{{ step }}</div>
              </div>
            </div>
          </div>
          
          <!-- 漏洞URL -->
          <div class="section">
            <div class="section-icon">🔗</div>
            <div class="section-title">漏洞URL</div>
            <div class="section-content">
              <a :href="vuln.url" target="_blank" class="tech-link">{{ vuln.url }}</a>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 🔥 攻击路径 -->
      <el-card v-if="report.attack_path && report.attack_path.length > 0" shadow="hover" class="attack-path-card tech-card">
        <template #header>
          <h2 class="tech-text">🎯 攻击路径</h2>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="(step, index) in report.attack_path"
            :key="index"
            :type="index === report.attack_path.length - 1 ? 'success' : 'primary'"
            class="tech-timeline-item"
          >
            <div class="attack-step">
              <div class="attack-step-header">
                <span class="step-badge">Step {{ step.step }}</span>
                <span class="action-badge">{{ step.action }}</span>
              </div>
              <div class="attack-step-desc">{{ step.description }}</div>
              <div class="attack-step-meta">
                <el-tag size="small" class="tool-tag">🛠️ {{ step.tool }}</el-tag>
                <span class="result-text">→ {{ step.result }}</span>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 统计信息 -->
      <el-card shadow="hover" class="stats-card tech-card">
        <template #header>
          <h2 class="tech-text">📈 统计信息</h2>
        </template>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">总轮数</div>
              <div class="stat-value tech-value">{{ report.statistics?.total_rounds || 0 }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">成功率</div>
              <div class="stat-value tech-value">
                {{ ((report.statistics?.success_rate || 0) * 100).toFixed(1) }}%
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">工具调用</div>
              <div class="stat-value tech-value">{{ getTotalToolCalls() }}</div>
            </div>
          </el-col>
        </el-row>

        <el-divider />

        <h3 class="tech-text-secondary">漏洞严重程度分布</h3>
        <el-row :gutter="20" style="margin-top: 15px;">
          <el-col :span="6" v-for="(count, severity) in report.statistics?.vuln_by_severity" :key="severity">
            <div class="severity-stat">
              <el-tag :type="getSeverityType(severity.toUpperCase())" class="tech-tag">
                {{ severity.toUpperCase() }}
              </el-tag>
              <span class="count tech-value">{{ count }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 建议 -->
      <el-card v-if="report.recommendations && report.recommendations.length > 0" shadow="hover" class="recommendations-card tech-card">
        <template #header>
          <h2 class="tech-text">💡 修复建议</h2>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="(rec, index) in report.recommendations"
            :key="index"
            type="primary"
            class="tech-timeline-item"
          >
            {{ rec }}
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>

    <el-empty v-else description="未找到报告" class="tech-empty" />

    <!-- 证据对话框 -->
    <el-dialog v-model="evidenceDialogVisible" title="漏洞证据" width="70%" class="tech-dialog">
      <pre class="evidence-content">{{ currentEvidence }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { ArrowLeft, Download, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const taskId = ref(route.params.id as string)
const report = ref<any>(null)
const loading = ref(true)
const evidenceDialogVisible = ref(false)
const currentEvidence = ref('')
const particleCanvas = ref<HTMLCanvasElement | null>(null)

// 🔥 粒子动画
let animationId: number

const initParticles = () => {
  if (!particleCanvas.value) return

  const canvas = particleCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const particles: any[] = []
  const particleCount = 50

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: Math.random() * 2 + 1
    })
  }

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.fillStyle = 'rgba(0, 255, 255, 0.5)'

    particles.forEach((p, i) => {
      p.x += p.vx
      p.y += p.vy

      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1

      ctx.beginPath()
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
      ctx.fill()

      // 连线
      particles.slice(i + 1).forEach(p2 => {
        const dx = p.x - p2.x
        const dy = p.y - p2.y
        const dist = Math.sqrt(dx * dx + dy * dy)

        if (dist < 150) {
          ctx.strokeStyle = `rgba(0, 255, 255, ${0.2 * (1 - dist / 150)})`
          ctx.lineWidth = 1
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.stroke()
        }
      })
    })

    animationId = requestAnimationFrame(animate)
  }

  animate()
}

const statusText = computed(() => {
  const map: any = {
    completed: '已完成',
    no_findings: '未发现漏洞'
  }
  return map[report.value?.summary?.status] || report.value?.summary?.status
})

const loadReport = async () => {
  loading.value = true
  
  // 🔥🔥🔥 DEBUG: 打印请求URL
  const apiUrl = `http://localhost:8000/api/v1/tasks/${taskId.value}`
  console.log('🔍 [Report.vue] 请求URL:', apiUrl)
  console.log('🔍 [Report.vue] TaskID:', taskId.value)
  
  try {
    // 🔥 从Task API获取完整任务信息（包含report字段）
    const { data } = await axios.get(apiUrl)
    
    console.log('✅ [Report.vue] API返回数据:', data)
    
    if (data.report) {
      report.value = data.report
      console.log('✅ [Report.vue] 报告加载成功:', report.value)
    } else {
      console.warn('⚠️ [Report.vue] Task.report为空')
      ElMessage.warning('任务尚未生成报告')
    }
  } catch (error: any) {
    console.error('❌ [Report.vue] 加载报告失败:', error)
    console.error('❌ [Report.vue] 错误详情:', {
      message: error.message,
      status: error.response?.status,
      url: error.config?.url,
      method: error.config?.method
    })
    
    if (error.response?.status === 404) {
      ElMessage.error('任务不存在')
    } else {
      ElMessage.error('加载报告失败: ' + (error.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

const getSeverityType = (severity: string) => {
  const map: any = {
    CRITICAL: 'danger',
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'info',
    INFO: ''
  }
  return map[severity?.toUpperCase()] || 'info'
}

const getTotalToolCalls = () => {
  const toolUsage = report.value?.statistics?.tool_usage || {}
  return Object.values(toolUsage).reduce((sum: number, count: any) => sum + count, 0)
}

const copyFlag = (flag: string) => {
  navigator.clipboard.writeText(flag)
  ElMessage.success('FLAG 已复制到剪贴板')
}

const showEvidence = (vuln: any) => {
  currentEvidence.value = vuln.evidence
  evidenceDialogVisible.value = true
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const exportReport = () => {
  const blob = new Blob([JSON.stringify(report.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `report_${taskId.value}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

onMounted(() => {
  loadReport()
  initParticles()
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})
</script>

<style scoped>
/* 🔥 科技风背景 */
.report-page {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.tech-background {
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
}

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
    linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  z-index: 0;
  pointer-events: none;
}

/* 🔥 内容区域 */
.report-header,
.report-content,
.loading,
.tech-empty {
  position: relative;
  z-index: 1;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  margin-bottom: 20px;
}

.tech-title {
  margin: 0;
  font-size: 28px;
  font-weight: bold;
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  gap: 15px;
}

.report-content {
  padding: 0 20px 40px;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 🔥 卡片样式 */
.tech-card {
  background: rgba(26, 31, 58, 0.8) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 255, 255, 0.2) !important;
  box-shadow: 0 8px 32px rgba(0, 255, 255, 0.1) !important;
  transition: all 0.3s ease;
}

.tech-card:hover {
  border-color: rgba(0, 255, 255, 0.4) !important;
  box-shadow: 0 12px 48px rgba(0, 255, 255, 0.2) !important;
  transform: translateY(-2px);
}

.tech-card :deep(.el-card__header) {
  background: rgba(0, 255, 255, 0.05);
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
}

/* 🔥 文字样式 */
.tech-text {
  color: #00ffff;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.tech-text-secondary {
  color: #00ff88;
  font-weight: 500;
}

.tech-value {
  color: #00ffff;
  font-weight: bold;
  font-size: 1.1em;
}

.mono-text {
  font-family: 'Courier New', monospace;
  color: #a0d5ff;
}

/* 🔥 按钮 */
.glow-button {
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%) !important;
  border: none !important;
  color: #0a0e27 !important;
  font-weight: bold !important;
  box-shadow: 0 4px 15px rgba(0, 255, 255, 0.4) !important;
  transition: all 0.3s ease !important;
}

.glow-button:hover {
  box-shadow: 0 6px 25px rgba(0, 255, 255, 0.6) !important;
  transform: translateY(-2px);
}

.glow-button-small {
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%) !important;
  border: none !important;
  color: #0a0e27 !important;
  font-weight: bold !important;
}

/* 🔥 Section Header */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 0;
}

.icon-badge {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 136, 0.2));
  border-radius: 10px;
  font-size: 20px;
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
}

.header-text {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 0.5px;
}

.count-badge {
  margin-left: auto;
  background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(0, 255, 136, 0.15));
  color: #00ffff;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  border: 1px solid rgba(0, 255, 255, 0.3);
}

/* 🔥 Summary Section */
.summary-section {
  background: linear-gradient(135deg, rgba(13, 17, 40, 0.95), rgba(26, 31, 58, 0.95));
  border: 1px solid rgba(0, 255, 255, 0.15);
  border-radius: 16px;
  padding: 32px;
  backdrop-filter: blur(20px);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  position: relative;
  overflow: hidden;
}

.summary-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.5), transparent);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.summary-item {
  background: rgba(0, 255, 255, 0.03);
  border: 1px solid rgba(0, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.summary-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, #00ffff, #00ff88);
  opacity: 0;
  transition: opacity 0.3s;
}

.summary-item:hover {
  background: rgba(0, 255, 255, 0.06);
  border-color: rgba(0, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 255, 255, 0.15);
}

.summary-item:hover::before {
  opacity: 1;
}

.highlight-item {
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.2);
}

.highlight-item::after {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(0, 255, 255, 0.1), transparent);
  pointer-events: none;
}

.item-label {
  font-size: 12px;
  color: #8b95a5;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
  font-weight: 600;
}

.item-value {
  font-size: 16px;
  color: #e8eaed;
  font-weight: 500;
}

.url-value {
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 13px;
  color: #00d4ff;
  word-break: break-all;
  line-height: 1.6;
}

.number-value {
  font-size: 32px;
  font-weight: 700;
  color: #00ffff;
  font-family: 'SF Mono', 'Monaco', monospace;
  text-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
}

.highlight-number {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.big-number {
  font-size: 48px;
  background: linear-gradient(135deg, #00ffff, #00ff88);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.unit {
  font-size: 16px;
  color: #00ff88;
  font-weight: 600;
}

.mode-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.mode-ctf {
  background: linear-gradient(135deg, rgba(255, 59, 92, 0.15), rgba(255, 92, 59, 0.15));
  color: #ff6b6b;
  border: 1px solid rgba(255, 59, 92, 0.3);
}

.mode-real {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.15));
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.status-success {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.15));
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-pending {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.15));
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.time-value {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  color: #94a3b8;
}

/* 🔥 FLAGS Section */
.flags-section {
  background: linear-gradient(135deg, rgba(13, 17, 40, 0.95), rgba(26, 31, 58, 0.95));
  border: 1px solid rgba(0, 255, 255, 0.15);
  border-radius: 16px;
  padding: 32px;
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.flags-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.flag-item {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(0, 255, 255, 0.03);
  border: 1px solid rgba(0, 255, 255, 0.15);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.flag-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #00ffff, #00ff88);
  transform: scaleY(0);
  transition: transform 0.3s;
}

.flag-item:hover {
  background: rgba(0, 255, 255, 0.06);
  border-color: rgba(0, 255, 255, 0.3);
  transform: translateX(4px);
  box-shadow: 0 8px 24px rgba(0, 255, 255, 0.2);
}

.flag-item:hover::before {
  transform: scaleY(1);
}

.flag-index {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(0, 255, 136, 0.15));
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 18px;
  font-weight: 700;
  color: #00ffff;
  font-family: 'SF Mono', monospace;
}

.flag-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.flag-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.flag-text {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 15px;
  color: #00ff88;
  background: rgba(0, 255, 136, 0.05);
  padding: 12px 20px;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  word-break: break-all;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.copy-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(0, 255, 255, 0.1);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 8px;
  color: #00ffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: rgba(0, 255, 255, 0.2);
  border-color: rgba(0, 255, 255, 0.5);
  transform: scale(1.05);
}

.copy-btn:active {
  transform: scale(0.95);
}

.copy-icon {
  font-size: 14px;
}

/* 🔥 标签 */
.tech-tag {
  border: 1px solid rgba(0, 255, 255, 0.3);
  background: rgba(0, 255, 255, 0.1) !important;
  font-weight: bold;
}

.flag-tag {
  font-size: 14px !important;
  padding: 8px 16px !important;
}

/* 🔥 漏洞详情卡片 */
.vuln-detail-card {
  background: rgba(10, 14, 39, 0.6);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.vuln-detail-card:hover {
  border-color: rgba(0, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(0, 255, 255, 0.3);
  transform: translateY(-3px);
}

.vuln-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
}

.severity-tag {
  font-size: 16px !important;
  font-weight: bold !important;
  padding: 6px 16px !important;
}

.vuln-title {
  color: #00ffff;
  font-size: 20px;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.cvss-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding: 12px;
  background: rgba(0, 255, 255, 0.05);
  border-radius: 8px;
}

.cvss-label {
  color: #a0a0a0;
  font-size: 14px;
}

.cvss-value {
  color: #00ffff;
  font-size: 18px;
  font-weight: bold;
}

.section {
  margin-bottom: 20px;
}

.section-icon {
  font-size: 18px;
  margin-bottom: 8px;
}

.section-title {
  color: #00ff88;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.section-content {
  color: #e0e0e0;
  line-height: 1.6;
  padding-left: 10px;
}

/* 🔥 复现步骤 */
.reproduction-steps {
  padding-left: 10px;
}

.repro-step {
  display: flex;
  gap: 15px;
  margin-bottom: 12px;
  align-items: flex-start;
}

.step-number {
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%);
  color: #0a0e27;
  border-radius: 50%;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
}

.step-content {
  color: #e0e0e0;
  line-height: 1.6;
  padding-top: 5px;
  font-family: 'Courier New', monospace;
  background: rgba(0, 255, 255, 0.03);
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 3px solid #00ffff;
}

/* 🔥 攻击路径 */
.attack-step {
  background: rgba(10, 14, 39, 0.6);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 10px;
  padding: 20px;
  margin-top: -10px;
}

.attack-step-header {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.step-badge {
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%);
  color: #0a0e27;
  padding: 4px 12px;
  border-radius: 16px;
  font-weight: bold;
  font-size: 13px;
}

.action-badge {
  background: rgba(0, 255, 255, 0.15);
  color: #00ffff;
  padding: 4px 12px;
  border-radius: 16px;
  font-weight: bold;
  font-size: 13px;
  border: 1px solid rgba(0, 255, 255, 0.3);
}

.attack-step-desc {
  color: #e0e0e0;
  line-height: 1.6;
  margin-bottom: 12px;
}

.attack-step-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tool-tag {
  background: rgba(0, 255, 255, 0.1) !important;
  border: 1px solid rgba(0, 255, 255, 0.3) !important;
  color: #00ff88 !important;
}

.result-text {
  color: #00ffff;
  font-style: italic;
}

/* 🔥 链接 */
.tech-link {
  color: #00ffff;
  text-decoration: none;
  transition: all 0.3s ease;
}

.tech-link:hover {
  color: #00ff88;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

/* 🔥 统计卡片 */
.stat-item {
  text-align: center;
  padding: 25px;
  background: rgba(0, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: rgba(0, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 255, 255, 0.2);
  transform: translateY(-3px);
}

.stat-label {
  font-size: 14px;
  color: #a0a0a0;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #00ffff;
  text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
}

.severity-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: rgba(0, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 255, 0.2);
  margin-bottom: 10px;
  transition: all 0.3s ease;
}

.severity-stat:hover {
  background: rgba(0, 255, 255, 0.1);
  transform: translateX(5px);
}

.severity-stat .count {
  font-size: 24px;
  font-weight: bold;
}

/* 🔥 证据内容 */
.evidence-content {
  background: rgba(10, 14, 39, 0.9);
  padding: 20px;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 255, 0.2);
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #00ff88;
  font-family: 'Courier New', monospace;
}

/* 🔥 时间线 */
.tech-timeline-item :deep(.el-timeline-item__content) {
  color: #e0e0e0;
}

.tech-timeline-item :deep(.el-timeline-item__node) {
  background: #00ffff;
  border-color: #00ffff;
}

/* 🔥 空状态 */
.tech-empty :deep(.el-empty__description) {
  color: #00ffff;
}

/* 🔥 对话框 */
.tech-dialog :deep(.el-dialog) {
  background: rgba(26, 31, 58, 0.95);
  border: 1px solid rgba(0, 255, 255, 0.3);
}

.tech-dialog :deep(.el-dialog__header) {
  background: rgba(0, 255, 255, 0.1);
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
}

.tech-dialog :deep(.el-dialog__title) {
  color: #00ffff;
}

/* 🔥 响应式 */
@media (max-width: 768px) {
  .report-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .tech-title {
    font-size: 22px;
  }
}
</style>
