<template>
  <div class="space-y-3 max-h-64 overflow-y-auto">
    <div 
      v-for="(activity, index) in activities" 
      :key="index"
      class="flex items-start gap-4 p-3 rounded-lg bg-dark-700"
    >
      <div 
        class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
        :class="iconBgClass(activity.type)"
      >
        <component :is="iconComponent(activity.type)" class="w-4 h-4 text-white" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between mb-1">
          <span class="text-sm text-white truncate">{{ activity.message }}</span>
          <span class="text-xs text-gray-500 flex-shrink-0 ml-2">{{ activity.time }}</span>
        </div>
        <span class="text-xs text-gray-500">{{ activity.agent }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-vue-next'

interface Activity {
  time: string
  type: string
  message: string
  agent: string
}

interface Props {
  activities: Activity[]
}

defineProps<Props>()

const iconComponent = (type: string) => {
  const icons: Record<string, any> = {
    success: CheckCircle,
    warning: AlertTriangle,
    error: AlertCircle,
    info: Info,
  }
  return icons[type] || Info
}

const iconBgClass = (type: string) => {
  const classes: Record<string, string> = {
    success: 'bg-cyber-green',
    warning: 'bg-cyber-orange',
    error: 'bg-cyber-red',
    info: 'bg-cyber-blue',
  }
  return classes[type] || 'bg-gray-500'
}
</script>
