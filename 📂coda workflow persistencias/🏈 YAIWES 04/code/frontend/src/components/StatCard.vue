<template>
  <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
    <div class="flex items-center gap-4">
      <!-- 图标 -->
      <div 
        class="w-14 h-14 rounded-xl flex items-center justify-center"
        :class="iconBgClass"
      >
        <component :is="iconComponent" class="w-7 h-7 text-white" />
      </div>
      
      <!-- 数值 -->
      <div class="flex-1">
        <p class="text-sm text-gray-400 mb-1">{{ title }}</p>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-bold text-white">{{ value }}</span>
          <span 
            class="text-sm font-medium"
            :class="changeClass"
          >
            {{ changePrefix }}{{ Math.abs(change) }}%
          </span>
        </div>
      </div>

      <!-- 趋势图 -->
      <div class="w-20 h-12">
        <MiniTrendChart :color="trendColor" :points="trendPoints" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Target, Radar, Bug, FileText } from 'lucide-vue-next'
import MiniTrendChart from './MiniTrendChart.vue'

interface Props {
  title: string
  value: number
  change: number
  trendPoints?: number[]
  icon: 'Target' | 'Radar' | 'Bug' | 'FileText'
  color: 'blue' | 'purple' | 'red' | 'green'
}

const props = defineProps<Props>()

const iconMap = {
  Target,
  Radar,
  Bug,
  FileText,
}

const iconComponent = computed(() => iconMap[props.icon])

const iconBgClass = computed(() => {
  const classes = {
    blue: 'bg-gradient-to-br from-cyber-blue to-blue-600',
    purple: 'bg-gradient-to-br from-cyber-purple to-purple-600',
    red: 'bg-gradient-to-br from-cyber-red to-red-600',
    green: 'bg-gradient-to-br from-cyber-green to-green-600',
  }
  return classes[props.color]
})

const changeClass = computed(() => {
  if (props.change > 0) return 'text-cyber-green'
  if (props.change < 0) return 'text-cyber-red'
  return 'text-gray-400'
})

const changePrefix = computed(() => {
  if (props.change > 0) return '+'
  if (props.change < 0) return '-'
  return ''
})

const trendColor = computed(() => {
  const colors = {
    blue: '#00d4ff',
    purple: '#8b5cf6',
    red: '#ef4444',
    green: '#10b981',
  }
  return colors[props.color]
})
</script>
