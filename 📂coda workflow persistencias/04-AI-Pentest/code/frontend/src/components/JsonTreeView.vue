<template>
  <div class="space-y-2 text-xs">
    <template v-if="isObjectLike(data)">
      <div
        v-for="(value, key) in normalizedEntries"
        :key="String(key)"
        class="rounded-lg border border-slate-700/60 bg-slate-950/60"
      >
        <button
          v-if="isObjectLike(value)"
          class="w-full flex items-center justify-between gap-3 px-3 py-2 text-left hover:bg-slate-800/50"
          @click="toggle(String(currentPath(key)))"
        >
          <span class="text-slate-300 break-all">
            <span class="text-cyan-300">{{ key }}</span>
            <span class="text-slate-500 ml-2">{{ getTypeLabel(value) }}</span>
          </span>
          <span class="text-slate-500">{{ expandedPaths[currentPath(key)] ? '收起' : '展开' }}</span>
        </button>
        <div v-else class="px-3 py-2 break-all">
          <span class="text-cyan-300">{{ key }}</span>
          <span class="text-slate-500 mx-2">=</span>
          <span class="text-slate-200">{{ formatPrimitive(value) }}</span>
        </div>

        <div v-if="isObjectLike(value) && expandedPaths[currentPath(key)]" class="px-3 pb-3">
          <JsonTreeView
            :data="value"
            :path="currentPath(key)"
            :expanded-paths="expandedPaths"
            @toggle="$emit('toggle', $event)"
          />
        </div>
      </div>
    </template>
    <div v-else class="rounded-lg border border-slate-700/60 bg-slate-950/60 px-3 py-2 text-slate-200 break-all">
      {{ formatPrimitive(data) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  data: unknown
  path?: string
  expandedPaths: Record<string, boolean>
}>()

const emit = defineEmits<{
  (e: 'toggle', path: string): void
}>()

const isObjectLike = (value: unknown): boolean => {
  return value !== null && typeof value === 'object'
}

const normalizedEntries = computed(() => {
  if (Array.isArray(props.data)) {
    return props.data.map((value, index) => [index, value])
  }
  if (isObjectLike(props.data)) {
    return Object.entries(props.data as Record<string, unknown>)
  }
  return []
})

const currentPath = (key: string | number): string => {
  return props.path ? `${props.path}.${String(key)}` : String(key)
}

const toggle = (path: string) => {
  emit('toggle', path)
}

const getTypeLabel = (value: unknown): string => {
  if (Array.isArray(value)) return `Array(${value.length})`
  if (value === null) return 'null'
  return 'Object'
}

const formatPrimitive = (value: unknown): string => {
  if (typeof value === 'string') return value
  if (value === null) return 'null'
  if (typeof value === 'undefined') return 'undefined'
  return String(value)
}
</script>
