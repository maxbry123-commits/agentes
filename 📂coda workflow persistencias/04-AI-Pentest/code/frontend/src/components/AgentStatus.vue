<template>
  <div class="space-y-3">
    <div 
      v-for="agent in agents" 
      :key="agent.name"
      class="flex items-center justify-between p-3 rounded-lg bg-dark-700"
    >
      <div class="flex items-center gap-3">
        <div 
          class="w-2 h-2 rounded-full"
          :class="statusDotClass(agent.status)"
        ></div>
        <span class="text-sm text-gray-300">{{ agent.name }}</span>
      </div>
      <span class="text-xs text-gray-500">{{ agent.lastActive }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Agent {
  name: string
  status: string
  lastActive: string
}

interface Props {
  agents: Agent[]
}

defineProps<Props>()

const statusDotClass = (status: string) => {
  const classes: Record<string, string> = {
    running: 'bg-cyber-green shadow-[0_0_8px_#10b981]',
    idle: 'bg-gray-500',
    error: 'bg-cyber-red shadow-[0_0_8px_#ef4444]',
  }
  return classes[status] || 'bg-gray-500'
}
</script>
