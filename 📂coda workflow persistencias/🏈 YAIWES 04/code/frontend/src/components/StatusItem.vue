<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <span class="text-sm text-gray-400">{{ label }}</span>
      <span class="text-sm font-medium text-white">{{ value }}%</span>
    </div>
    <div class="h-2 bg-dark-600 rounded-full overflow-hidden">
      <div 
        class="h-full rounded-full transition-all duration-500"
        :style="{ 
          width: `${value}%`,
          backgroundColor: color 
        }"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string
  value: number
  color: string
}

defineProps<Props>()
</script>
