<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { Plus, Play, Database, Radio } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

const navItems = [
  { path: '/session/new', label: '新建任务', icon: Plus },
  { path: '/', label: '任务列表', icon: Play },
  { path: '/kb', label: '知识库', icon: Database },
  { path: '/status', label: '连接测试', icon: Radio },
]

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <aside class="w-56 bg-white border-r flex flex-col shrink-0 h-full">
    <!-- Header -->
    <div class="px-4 py-3 border-b flex items-center gap-2">
      <div class="h-7 w-7 rounded bg-green-600 flex items-center justify-center text-white font-bold text-sm">C</div>
      <span class="font-semibold text-sm text-gray-800">CTF-Solver</span>
    </div>

    <!-- Nav Items -->
    <nav class="flex-1 p-2 space-y-0.5">
      <button
        v-for="item in navItems" :key="item.path"
        @click="navigate(item.path)"
        :class="[
          'w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors text-left',
          route.path === item.path
            ? 'bg-green-50 text-green-700 font-medium'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        ]"
      >
        <component :is="item.icon" class="h-4 w-4 shrink-0" />
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <!-- Footer -->
    <div class="p-3 border-t">
      <div class="text-xs text-gray-400">LLM-CTF-Solver v1.0</div>
    </div>
  </aside>
</template>
