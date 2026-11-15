<script setup lang="ts">
defineProps<{ flag: string }>()
</script>

<template>
  <div class="mx-4 mt-2 bg-primary/10 border border-primary rounded-lg px-4 py-3 flex items-center gap-3 flag-found">
    <div class="text-2xl">🎯</div>
    <div>
      <div class="text-sm font-bold text-primary">Flag Found!</div>
      <code class="text-sm text-primary font-mono">{{ flag }}</code>
    </div>
  </div>
</template>
