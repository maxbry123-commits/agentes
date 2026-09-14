<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ stats?: Record<string, unknown> }>()

const tokens = computed(() => {
  const t = Number(props.stats?.total_tokens ?? 0)
  if (t >= 1000) return (t / 1000).toFixed(1) + 'K'
  return String(t)
})
const cost = computed(() => {
  const c = Number(props.stats?.cost ?? 0)
  return '$' + c.toFixed(3)
})
</script>

<template>
  <div v-if="stats && Object.keys(stats).length" class="flex items-center gap-3 text-xs text-muted-foreground">
    <span>{{ tokens }} tokens</span>
    <span>{{ cost }}</span>
  </div>
</template>
