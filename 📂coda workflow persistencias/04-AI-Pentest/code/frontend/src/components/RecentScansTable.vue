<template>
  <div class="overflow-hidden">
    <table class="w-full">
      <thead>
        <tr class="border-b border-dark-500">
          <th class="text-left py-3 px-4 text-sm font-medium text-gray-400">目标</th>
          <th class="text-left py-3 px-4 text-sm font-medium text-gray-400">类型</th>
          <th class="text-left py-3 px-4 text-sm font-medium text-gray-400">状态</th>
          <th class="text-left py-3 px-4 text-sm font-medium text-gray-400">进度</th>
          <th class="text-left py-3 px-4 text-sm font-medium text-gray-400">时间</th>
          <th class="text-right py-3 px-4 text-sm font-medium text-gray-400">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr 
          v-for="scan in scans" 
          :key="scan.id"
          class="border-b border-dark-600 hover:bg-dark-700 transition-colors"
        >
          <td class="py-3 px-4">
            <div class="flex items-center gap-2">
              <Server class="w-4 h-4 text-cyber-blue" />
              <span class="text-sm text-white font-mono">{{ scan.target }}</span>
            </div>
          </td>
          <td class="py-3 px-4">
            <span class="text-sm text-gray-300">{{ scan.type }}</span>
          </td>
          <td class="py-3 px-4">
            <t-tag 
              :theme="statusTheme(scan.status)" 
              size="small"
            >
              {{ statusText(scan.status) }}
            </t-tag>
          </td>
          <td class="py-3 px-4">
            <div class="flex items-center gap-2">
              <div class="flex-1 h-1.5 bg-dark-600 rounded-full overflow-hidden">
                <div 
                  class="h-full rounded-full transition-all"
                  :class="progressClass(scan.status)"
                  :style="{ width: `${scan.progress}%` }"
                ></div>
              </div>
              <span class="text-xs text-gray-400">{{ scan.progress }}%</span>
            </div>
          </td>
          <td class="py-3 px-4">
            <span class="text-sm text-gray-400">{{ scan.time }}</span>
          </td>
          <td class="py-3 px-4 text-right">
            <t-button variant="text" size="small">
              详情
            </t-button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { Server } from 'lucide-vue-next'

interface Scan {
  id: number
  target: string
  type: string
  status: string
  time: string
  progress: number
}

interface Props {
  scans: Scan[]
}

defineProps<Props>()

const statusTheme = (status: string) => {
  const themes: Record<string, string> = {
    completed: 'success',
    running: 'primary',
    pending: 'warning',
    failed: 'danger',
  }
  return themes[status] || 'default'
}

const statusText = (status: string) => {
  const texts: Record<string, string> = {
    completed: '已完成',
    running: '进行中',
    pending: '等待中',
    failed: '失败',
  }
  return texts[status] || status
}

const progressClass = (status: string) => {
  const classes: Record<string, string> = {
    completed: 'bg-cyber-green',
    running: 'bg-cyber-blue',
    pending: 'bg-gray-500',
    failed: 'bg-cyber-red',
  }
  return classes[status] || 'bg-gray-500'
}
</script>
