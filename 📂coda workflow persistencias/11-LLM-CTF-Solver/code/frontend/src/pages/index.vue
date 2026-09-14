<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/request'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import type { TaskInfo } from '@/utils/interface'

const router = useRouter()
const tasks = ref<TaskInfo[]>([])
const loading = ref(true)
const taskStatuses = ref<Record<string, string>>({})

async function refreshStatuses() {
  const results = await Promise.allSettled(
    tasks.value.map((t) => api.get(`/task/${t.task_id}/status`))
  )
  for (const r of results) {
    if (r.status === 'fulfilled' && r.value.data?.task_id) {
      taskStatuses.value[r.value.data.task_id] = r.value.data.status
    }
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/task/')
    tasks.value = data.tasks ?? []
    await refreshStatuses()
  } catch { /* ignore */ }
  loading.value = false
})
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">LLM-CTF-Solver</h1>
        <p class="text-muted-foreground">CTF 自动解题 / 授权渗透测试</p>
      </div>
      <Button @click="router.push('/session/new')">
        新建任务
      </Button>
    </div>

    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 3" :key="i" class="h-20 w-full" />
    </div>

    <div v-else-if="tasks.length === 0" class="text-center py-20">
      <p class="text-muted-foreground text-lg">暂无历史任务</p>
      <p class="text-muted-foreground text-sm mt-2">点击"新建任务"开始你的第一次 CTF 解题或渗透测试</p>
    </div>

    <div v-else class="grid gap-4">
      <Card v-for="t in tasks" :key="t.task_id" class="hover:border-primary/50 cursor-pointer transition-colors"
           @click="router.push('/session/' + t.task_id)">
        <CardHeader class="pb-2">
          <div class="flex items-center justify-between">
            <CardTitle class="text-base">{{ t.task_id }}</CardTitle>
            <Badge :variant="(taskStatuses[t.task_id] || t.status) === 'processing' ? 'default' : 'secondary'">
              {{ taskStatuses[t.task_id] || t.status || 'completed' }}
            </Badge>
          </div>
          <CardDescription>
            {{ t.mode?.toUpperCase() }} · {{ t.message_count ?? 0 }} messages
            · {{ t.created_at ? new Date(t.created_at).toLocaleString() : '' }}
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  </div>
</template>
