<template>
  <div class="space-y-6">
    <!-- 报告列表 -->
    <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-white">测试报告</h3>
        <div class="flex items-center gap-4">
          <t-date-range-picker v-model="dateRange" clearable />
          <t-input v-model="searchQuery" placeholder="搜索报告..." class="w-64" />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-6">
        <div 
          v-for="report in filteredReports" 
          :key="report.id"
          class="p-6 rounded-xl bg-dark-700 border border-dark-500 card-hover cursor-pointer"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-cyber-purple/20 flex items-center justify-center">
                <FileText class="w-6 h-6 text-cyber-purple" />
              </div>
              <div>
                <h4 class="text-white font-medium">{{ report.name }}</h4>
                <p class="text-sm text-gray-400">{{ report.target }}</p>
              </div>
            </div>
            <t-tag :theme="riskTheme(report.risk_level)" size="small">
              {{ riskText(report.risk_level) }}
            </t-tag>
          </div>

          <div class="grid grid-cols-3 gap-4 mb-4">
            <div class="text-center p-2 rounded-lg bg-dark-600">
              <p class="text-lg font-bold text-white">{{ report.vulns }}</p>
              <p class="text-xs text-gray-400">漏洞数</p>
            </div>
            <div class="text-center p-2 rounded-lg bg-dark-600">
              <p class="text-lg font-bold text-cyber-green">{{ formatSuccessRate(report.success_rate) }}</p>
              <p class="text-xs text-gray-400">成功率</p>
            </div>
            <div class="text-center p-2 rounded-lg bg-dark-600">
              <p class="text-lg font-bold text-gray-300">{{ formatDuration(report) }}</p>
              <p class="text-xs text-gray-400">耗时</p>
            </div>
          </div>

          <div class="flex items-center justify-between pt-4 border-t border-dark-500">
            <span class="text-sm text-gray-500">{{ report.created_at }}</span>
            <div class="flex items-center gap-2">
              <t-button
                v-for="format in availableFormats(report)"
                :key="`${report.id}-${format}`"
                variant="outline"
                size="small"
                @click.stop="downloadReport(report.id, format)"
              >
                <Download class="w-4 h-4 mr-1" />
                {{ formatLabel(format) }}
              </t-button>
              <t-button variant="primary" size="small" @click.stop="viewReport(report)">
                查看
              </t-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { FileText, Download } from 'lucide-vue-next'
import { reportApi } from '../api'
import { MessagePlugin } from 'tdesign-vue-next'

interface Report {
  id: string
  task_id?: string
  name: string
  target: string
  vulns: number
  success_rate?: number
  duration_seconds?: number
  duration?: string
  risk_level: string
  created_at: string
  formats?: string[]
}

const searchQuery = ref('')
const dateRange = ref([])
const reports = ref<Report[]>([])
const loading = ref(false)

// 过滤后的报告列表
const filteredReports = computed(() => {
  let result = reports.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(r => 
      r.name.toLowerCase().includes(query) ||
      r.target.toLowerCase().includes(query)
    )
  }
  return result
})

// 加载报告列表
const loadReports = async () => {
  loading.value = true
  try {
    const res = await reportApi.list() as any
    reports.value = res.reports || []
  } catch (error) {
    console.error('Failed to load reports:', error)
    MessagePlugin.error('加载报告失败')
  } finally {
    loading.value = false
  }
}

// 下载报告
const downloadReport = (taskId: string, format: string) => {
  const url = reportApi.download(taskId, format)
  window.open(url, '_blank')
}

// 查看报告详情
const viewReport = async (report: Report) => {
  try {
    const res = await reportApi.get(report.id) as any
    console.log('Report details:', res)
    MessagePlugin.success('报告详情已加载')
  } catch (error) {
    MessagePlugin.error('获取报告详情失败')
  }
}

const availableFormats = (report: Report) => {
  const formats = Array.isArray(report.formats) ? report.formats : ['html', 'markdown', 'json']
  return formats.filter((format) => ['html', 'markdown', 'json'].includes(format))
}

const formatLabel = (format: string) => {
  const labels: Record<string, string> = {
    html: 'HTML',
    markdown: 'Markdown',
    json: 'JSON',
  }
  return labels[format] || format.toUpperCase()
}

const formatSuccessRate = (value?: number) => `${Number.isFinite(value) ? value : 0}%`

const formatDuration = (report: Report) => {
  if (report.duration) return report.duration
  const totalSeconds = report.duration_seconds || 0
  if (totalSeconds <= 0) return '0s'
  if (totalSeconds < 60) return `${totalSeconds}s`
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  if (minutes < 60) return `${minutes}m ${seconds}s`
  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  return `${hours}h ${remainMinutes}m`
}

const riskTheme = (level: string) => {
  const themes: Record<string, string> = {
    critical: 'danger',
    high: 'warning',
    medium: 'warning',
    low: 'success',
  }
  return themes[level] || 'default'
}

const riskText = (level: string) => {
  const texts: Record<string, string> = {
    critical: '严重',
    high: '高危',
    medium: '中危',
    low: '低危',
  }
  return texts[level] || level
}

onMounted(() => {
  loadReports()
})
</script>
