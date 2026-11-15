<script setup lang="ts">
defineProps<{ phase: string }>()
const phases: Record<string, { label: string; color: string }> = {
  recon: { label: '侦察', color: 'bg-cyan-500' },
  exploit: { label: '利用', color: 'bg-yellow-500' },
  report: { label: '报告', color: 'bg-green-500' },
}
</script>

<template>
  <div class="flex items-center gap-1.5">
    <div :class="['h-2 w-2 rounded-full', phases[phase]?.color ?? 'bg-muted-foreground']" />
    <span class="text-xs text-muted-foreground">{{ phases[phase]?.label ?? phase }}</span>
  </div>
</template>
