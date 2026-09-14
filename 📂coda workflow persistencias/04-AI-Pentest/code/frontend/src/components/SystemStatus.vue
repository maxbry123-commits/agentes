<template>
  <div class="space-y-4">
    <StatusItem label="CPU使用率" :value="status.cpu" color="#00d4ff" />
    <StatusItem label="内存使用" :value="status.memory" color="#8b5cf6" />
    <StatusItem label="磁盘空间" :value="status.disk" color="#10b981" />
    <StatusItem label="网络带宽" :value="status.network" color="#f59e0b" />
  </div>
</template>

<script setup lang="ts">
import StatusItem from './StatusItem.vue'

interface Status {
  cpu: number
  memory: number
  disk: number
  network: number
}

interface Props {
  status: Status
}

defineProps<Props>()
</script>
