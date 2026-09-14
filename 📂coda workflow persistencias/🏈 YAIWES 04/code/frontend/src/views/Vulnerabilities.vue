<template>
  <div class="space-y-6">
    <!-- 漏洞统计 -->
    <div class="grid grid-cols-4 gap-6">
      <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center">
            <AlertOctagon class="w-6 h-6 text-red-500" />
          </div>
          <div>
            <p class="text-2xl font-bold text-white">{{ vulnStats.critical }}</p>
            <p class="text-sm text-gray-400">严重漏洞</p>
          </div>
        </div>
      </div>
      <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center">
            <AlertTriangle class="w-6 h-6 text-orange-500" />
          </div>
          <div>
            <p class="text-2xl font-bold text-white">{{ vulnStats.high }}</p>
            <p class="text-sm text-gray-400">高危漏洞</p>
          </div>
        </div>
      </div>
      <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-yellow-500/20 flex items-center justify-center">
            <AlertCircle class="w-6 h-6 text-yellow-500" />
          </div>
          <div>
            <p class="text-2xl font-bold text-white">{{ vulnStats.medium }}</p>
            <p class="text-sm text-gray-400">中危漏洞</p>
          </div>
        </div>
      </div>
      <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
            <Info class="w-6 h-6 text-green-500" />
          </div>
          <div>
            <p class="text-2xl font-bold text-white">{{ vulnStats.low }}</p>
            <p class="text-sm text-gray-400">低危漏洞</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 漏洞列表 -->
    <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-white">漏洞列表</h3>
        <div class="flex items-center gap-4">
          <t-select v-model="severityFilter" placeholder="严重程度" clearable>
            <t-option value="critical" label="严重" />
            <t-option value="high" label="高危" />
            <t-option value="medium" label="中危" />
            <t-option value="low" label="低危" />
          </t-select>
          <t-input v-model="searchQuery" placeholder="搜索漏洞..." class="w-64" />
        </div>
      </div>

      <div v-if="filteredVulns.length === 0" class="text-center py-12 text-gray-400">
        暂无漏洞数据
      </div>

      <div v-else class="space-y-4">
        <div 
          v-for="vuln in filteredVulns" 
          :key="vuln.id"
          class="p-4 rounded-lg bg-dark-700 border border-dark-500 hover:border-cyber-blue transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex items-start gap-4">
              <div 
                class="w-10 h-10 rounded-lg flex items-center justify-center"
                :class="severityBgClass(vuln.severity)"
              >
                <Bug class="w-5 h-5 text-white" />
              </div>
              <div>
                <div class="flex items-center gap-3 mb-2">
                  <h4 class="text-white font-medium">{{ vuln.name }}</h4>
                  <t-tag :theme="severityTheme(vuln.severity)" size="small">
                    {{ severityText(vuln.severity) }}
                  </t-tag>
                  <t-tag v-if="vuln.cve" variant="outline" size="small">{{ vuln.cve }}</t-tag>
                </div>
                <p class="text-sm text-gray-400 mb-2">{{ vuln.description }}</p>
                <div class="flex items-center gap-4 text-xs text-gray-500">
                  <span>目标: {{ vuln.target }}</span>
                  <span>发现时间: {{ vuln.discovered_at }}</span>
                </div>
              </div>
            </div>
            <t-tag :theme="statusTheme(vuln.status)" size="small">
              {{ statusText(vuln.status) }}
            </t-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { AlertOctagon, AlertTriangle, AlertCircle, Info, Bug } from 'lucide-vue-next'
import { vulnerabilityApi } from '../api'

const route = useRoute()
const vulnStats = ref({ critical: 0, high: 0, medium: 0, low: 0, total: 0 })
const vulnerabilities = ref<any[]>([])
const severityFilter = ref('')
const routeSeverityFilters = ref<string[]>([])
const searchQuery = ref('')

const filteredVulns = computed(() => {
  let result = vulnerabilities.value
  const activeSeverities = severityFilter.value
    ? [severityFilter.value]
    : routeSeverityFilters.value
  if (activeSeverities.length) {
    result = result.filter(v => activeSeverities.includes(v.severity))
  }
  if (searchQuery.value) {
    result = result.filter(v => 
      v.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  return result
})

const severityBgClass = (severity: string) => {
  const classes: Record<string, string> = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-green-500',
  }
  return classes[severity] || 'bg-gray-500'
}

const severityTheme = (severity: string) => {
  const themes: Record<string, string> = {
    critical: 'danger', high: 'warning', medium: 'warning', low: 'success',
  }
  return themes[severity] || 'default'
}

const severityText = (severity: string) => {
  const texts: Record<string, string> = {
    critical: '严重', high: '高危', medium: '中危', low: '低危',
  }
  return texts[severity] || severity
}

const statusTheme = (status: string) => {
  const themes: Record<string, string> = {
    open: 'danger', fixed: 'success', ignored: 'default',
  }
  return themes[status] || 'default'
}

const statusText = (status: string) => {
  const texts: Record<string, string> = {
    open: '未修复', fixed: '已修复', ignored: '已忽略',
  }
  return texts[status] || status
}

const loadData = async () => {
  try {
    const stats = await vulnerabilityApi.getStats() as any
    vulnStats.value = stats
    
    const data = await vulnerabilityApi.list() as any
    vulnerabilities.value = data.vulnerabilities || []
  } catch (error) {
    console.error('加载漏洞数据失败:', error)
  }
}

const syncFiltersFromRoute = () => {
  const severity = route.query.severity
  const search = route.query.search
  routeSeverityFilters.value = typeof severity === 'string'
    ? severity.split(',').map(item => item.trim()).filter(Boolean)
    : []
  severityFilter.value = routeSeverityFilters.value.length === 1 ? routeSeverityFilters.value[0] : ''
  searchQuery.value = typeof search === 'string' ? search : ''
}

onMounted(() => {
  syncFiltersFromRoute()
  loadData()
})

watch(
  () => route.query,
  () => {
    syncFiltersFromRoute()
  },
  { deep: true }
)

watch([severityFilter, searchQuery], loadData)
</script>
