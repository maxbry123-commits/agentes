<template>
  <div class="space-y-6">
    <!-- 顶部操作栏 -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <t-input 
          v-model="searchQuery" 
          placeholder="搜索目标..."
          class="w-80"
        >
          <template #prefix-icon>
            <Search class="w-4 h-4" />
          </template>
        </t-input>
        <t-select 
          v-model="statusFilter" 
          placeholder="状态筛选"
          class="w-40"
          clearable
        >
          <t-option value="active" label="活跃" />
          <t-option value="completed" label="已完成" />
          <t-option value="pending" label="待处理" />
        </t-select>
      </div>
      <t-button theme="primary" @click="showAddDialog = true">
        <Plus class="w-4 h-4 mr-2" />
        添加目标
      </t-button>
    </div>

    <!-- 目标卡片网格 -->
    <div class="grid grid-cols-3 gap-6">
      <div 
        v-for="target in filteredTargets" 
        :key="target.id"
        class="bg-dark-800 rounded-xl p-6 border border-dark-500 card-hover cursor-pointer"
        @click="viewTarget(target)"
      >
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-dark-600 flex items-center justify-center">
              <Server class="w-5 h-5 text-cyber-blue" />
            </div>
            <div>
              <h4 class="text-white font-medium">{{ target.name }}</h4>
              <p class="text-sm text-gray-400 font-mono">{{ target.ip }}</p>
            </div>
          </div>
          <t-tag :theme="statusTheme(target.status)" size="small">
            {{ statusText(target.status) }}
          </t-tag>
        </div>

        <div class="space-y-3 mb-4">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-400">操作系统</span>
            <span class="text-gray-300">{{ target.os }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-400">开放端口</span>
            <span class="text-gray-300">{{ target.open_ports }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-400">发现漏洞</span>
            <span class="text-cyber-red">{{ target.vulnerabilities }}</span>
          </div>
        </div>

        <div class="flex items-center justify-between pt-4 border-t border-dark-500">
          <span class="text-xs text-gray-500">最后扫描: {{ target.last_scan }}</span>
          <div class="flex items-center gap-2">
            <t-button variant="text" size="small">
              开始扫描
            </t-button>
            <t-button variant="text" size="small" theme="danger" @click.stop="deleteTarget(target.id)">
              <Trash class="w-4 h-4" />
            </t-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加目标对话框 -->
    <t-dialog 
      v-model:visible="showAddDialog"
      header="添加新目标"
      @confirm="addTarget"
    >
      <t-form :data="newTarget" label-align="top">
        <t-form-item label="目标名称" name="name">
          <t-input v-model="newTarget.name" placeholder="输入目标名称" />
        </t-form-item>
        <t-form-item label="IP/域名" name="ip">
          <t-input v-model="newTarget.ip" placeholder="输入IP地址或域名" />
        </t-form-item>
        <t-form-item label="描述" name="description">
          <t-textarea v-model="newTarget.description" placeholder="目标描述（可选）" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Plus, Server, Trash } from 'lucide-vue-next'
import { targetApi } from '../api'
import { MessagePlugin } from 'tdesign-vue-next'

interface Target {
  id: string
  name: string
  ip: string
  os: string
  open_ports: number
  vulnerabilities: number
  status: string
  last_scan: string
  description?: string
}

const searchQuery = ref('')
const statusFilter = ref('')
const showAddDialog = ref(false)
const targets = ref<Target[]>([])
const loading = ref(false)

const newTarget = ref({
  name: '',
  ip: '',
  description: '',
})

// 过滤后的目标列表
const filteredTargets = computed(() => {
  let result = targets.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.name.toLowerCase().includes(query) ||
      t.ip.toLowerCase().includes(query)
    )
  }
  if (statusFilter.value) {
    result = result.filter(t => t.status === statusFilter.value)
  }
  return result
})

// 加载目标列表
const loadTargets = async () => {
  loading.value = true
  try {
    const res = await targetApi.list() as any
    targets.value = res.targets || []
  } catch (error) {
    console.error('Failed to load targets:', error)
    MessagePlugin.error('加载目标列表失败')
  } finally {
    loading.value = false
  }
}

// 添加目标
const addTarget = async () => {
  if (!newTarget.value.name || !newTarget.value.ip) {
    MessagePlugin.warning('请填写目标名称和IP地址')
    return
  }
  
  try {
    await targetApi.create(newTarget.value)
    MessagePlugin.success('目标添加成功')
    showAddDialog.value = false
    newTarget.value = { name: '', ip: '', description: '' }
    loadTargets()
  } catch (error) {
    MessagePlugin.error('添加目标失败')
  }
}

// 删除目标
const deleteTarget = async (id: string) => {
  try {
    await targetApi.delete(id)
    MessagePlugin.success('目标已删除')
    loadTargets()
  } catch (error) {
    MessagePlugin.error('删除目标失败')
  }
}

// 查看目标详情
const viewTarget = (target: Target) => {
  console.log('View target:', target)
}

const statusTheme = (status: string) => {
  const themes: Record<string, string> = {
    active: 'primary',
    completed: 'success',
    pending: 'warning',
  }
  return themes[status] || 'default'
}

const statusText = (status: string) => {
  const texts: Record<string, string> = {
    active: '活跃',
    completed: '已完成',
    pending: '待处理',
  }
  return texts[status] || status
}

onMounted(() => {
  loadTargets()
})
</script>
