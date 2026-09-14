<template>
  <div class="space-y-6">
    <!-- 工具分类 -->
    <div class="grid grid-cols-3 md:grid-cols-6 gap-4">
      <div 
        v-for="category in toolCategories" 
        :key="category.name"
        class="bg-dark-800 rounded-xl p-4 border border-dark-500 card-hover cursor-pointer"
        :class="{ 'border-cyber-blue': selectedCategory === category.name }"
        @click="selectCategory(category.name)"
      >
        <div class="flex items-center gap-4">
          <div 
            class="w-12 h-12 rounded-xl flex items-center justify-center"
            :style="{ backgroundColor: category.color + '20' }"
          >
            <component :is="category.icon" class="w-6 h-6" :style="{ color: category.color }" />
          </div>
          <div>
            <h4 class="text-white font-medium">{{ category.name }}</h4>
            <p class="text-sm text-gray-400">{{ category.count }} 个工具</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 工具列表 -->
    <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-white">{{ selectedCategory || '所有工具' }}</h3>
        <t-input v-model="searchQuery" placeholder="搜索工具..." class="w-64" />
      </div>

      <div class="grid grid-cols-3 gap-4">
        <div 
          v-for="tool in filteredTools" 
          :key="tool.name"
          class="p-4 rounded-lg bg-dark-700 border border-dark-500 card-hover"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-dark-600 flex items-center justify-center">
                <Wrench class="w-5 h-5 text-cyber-blue" />
              </div>
              <div>
                <h4 class="text-white text-sm font-medium">{{ tool.name }}</h4>
                <p class="text-xs text-gray-400">{{ tool.category }}</p>
              </div>
            </div>
            <span 
              class="w-2 h-2 rounded-full"
              :class="tool.installed ? 'bg-cyber-green' : 'bg-gray-500'"
            ></span>
          </div>
          
          <p class="text-xs text-gray-400 mb-3">{{ tool.description }}</p>
          
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-500">v{{ tool.version }}</span>
            <t-button 
              :theme="tool.installed ? 'default' : 'primary'" 
              size="small"
            >
              {{ tool.installed ? '配置' : '安装' }}
            </t-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 工具状态 -->
    <div class="grid grid-cols-2 gap-6">
      <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
        <h3 class="text-lg font-semibold text-white mb-4">可用工具状态</h3>
        <div v-if="installedTools.length === 0" class="text-center py-8 text-gray-400">
          暂无已安装的工具
        </div>
        <div v-else class="space-y-3">
          <div 
            v-for="tool in installedTools" 
            :key="tool.name"
            class="flex items-center justify-between p-3 rounded-lg bg-dark-700"
          >
            <div class="flex items-center gap-3">
              <span class="w-2 h-2 rounded-full bg-cyber-green"></span>
              <span class="text-sm text-gray-300">{{ tool.name }}</span>
            </div>
            <span class="text-xs text-gray-500">v{{ tool.version }}</span>
          </div>
        </div>
      </div>

      <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
        <h3 class="text-lg font-semibold text-white mb-4">工具使用统计</h3>
        <div v-if="toolUsageStats.length === 0" class="text-center py-8 text-gray-400">
          暂无使用统计数据
        </div>
        <div v-else class="space-y-3">
          <div 
            v-for="stat in toolUsageStats" 
            :key="stat.name"
            class="flex items-center justify-between"
          >
            <span class="text-sm text-gray-400">{{ stat.name }}</span>
            <div class="flex items-center gap-2">
              <div class="w-32 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div 
                  class="h-full rounded-full" 
                  :style="{ width: stat.percentage + '%', backgroundColor: stat.color }"
                ></div>
              </div>
              <span class="text-xs text-gray-400">{{ stat.count }}次</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Wrench, Network, Globe, Lock, Shield } from 'lucide-vue-next'
import { systemApi } from '../api'
import { MessagePlugin } from 'tdesign-vue-next'

interface Tool {
  name: string
  category: string
  description: string
  version: string
  installed: boolean
  status: string
}

const selectedCategory = ref('')
const searchQuery = ref('')
const tools = ref<Tool[]>([])
const toolUsageStats = ref<{ name: string; count: number; percentage: number; color: string }[]>([])
const loading = ref(false)

const toolCategories = ref([
  { name: '网络扫描', count: 0, icon: Network, color: '#00d4ff' },
  { name: 'Web测试', count: 0, icon: Globe, color: '#8b5cf6' },
  { name: '暴力破解', count: 0, icon: Lock, color: '#f59e0b' },
  { name: '漏洞利用', count: 0, icon: Shield, color: '#ef4444' },
  { name: '信息收集', count: 0, icon: Network, color: '#10b981' },
  { name: '后渗透', count: 0, icon: Shield, color: '#f97316' },
])

// 已安装的工具列表
const installedTools = computed(() => 
  tools.value.filter(t => t.installed)
)

// 过滤后的工具列表
const filteredTools = computed(() => {
  let result = tools.value
  if (selectedCategory.value) {
    result = result.filter(t => t.category === selectedCategory.value)
  }
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.name.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query)
    )
  }
  return result
})

// 加载工具列表
const loadTools = async () => {
  loading.value = true
  try {
    const res = await systemApi.getTools() as any
    const toolList = res.tools || []
    
    // 处理工具数据
    tools.value = toolList.map((t: any) => ({
      name: t.name,
      category: getCategoryName(t.category),
      description: t.description || '',
      version: t.version || 'N/A',
      installed: t.installed,
      status: t.status || 'unknown'
    }))
    
    // 处理工具使用统计
    if (res.usage_stats) {
      toolUsageStats.value = res.usage_stats.map((s: any) => ({
        name: s.name,
        count: s.count || 0,
        percentage: s.percentage || 0,
        color: s.color || '#00d4ff'
      }))
    }
    
    // 更新分类计数
    updateCategoryCounts()
  } catch (error) {
    console.error('Failed to load tools:', error)
    MessagePlugin.error('加载工具列表失败')
  } finally {
    loading.value = false
  }
}

// 获取分类名称
const getCategoryName = (category: string): string => {
  const categoryMap: Record<string, string> = {
    'network': '网络扫描',
    'web': 'Web测试',
    'brute_force': '暴力破解',
    'exploit': '漏洞利用',
    'vulnerability': '漏洞扫描',
    'post_exploit': '后渗透',
    'recon': '信息收集',
    'wireless': '无线安全',
    'social_engineering': '社会工程',
    'forensics': '数字取证'
  }
  return categoryMap[category] || category
}

// 更新分类计数
const updateCategoryCounts = () => {
  const counts: Record<string, number> = {}
  tools.value.forEach(t => {
    counts[t.category] = (counts[t.category] || 0) + 1
  })
  
  toolCategories.value.forEach(cat => {
    cat.count = counts[cat.name] || 0
  })
}

const selectCategory = (name: string) => {
  selectedCategory.value = selectedCategory.value === name ? '' : name
}

onMounted(() => {
  loadTools()
})
</script>
