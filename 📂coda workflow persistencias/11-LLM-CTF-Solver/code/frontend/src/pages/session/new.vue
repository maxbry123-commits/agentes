<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/request'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'

const router = useRouter()
const mode = ref<'ctf' | 'pentest'>('ctf')
const autoMode = ref(true)
const problem = ref('')
const submitting = ref(false)
const error = ref('')

async function submit() {
  if (!problem.value.trim()) { error.value = '请输入题目或授权范围'; return }
  error.value = ''
  submitting.value = true
  try {
    const { data } = await api.post('/task/submit', {
      problem: problem.value,
      mode: mode.value,
      auto_mode: autoMode.value,
    })
    router.push('/session/' + data.task_id)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? '提交失败'
  }
  submitting.value = false
}
</script>

<template>
  <div class="p-6 max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold">新建任务</h1>

    <Card>
      <CardHeader><CardTitle>运行模式</CardTitle></CardHeader>
      <CardContent>
        <Tabs :model-value="mode" @update:model-value="(v) => mode = v as 'ctf' | 'pentest'">
          <TabsList>
            <TabsTrigger value="ctf">CTF 解题</TabsTrigger>
            <TabsTrigger value="pentest">渗透测试</TabsTrigger>
          </TabsList>
        </Tabs>
      </CardContent>
    </Card>

    <Card>
      <CardHeader><CardTitle>交互模式</CardTitle></CardHeader>
      <CardContent class="flex items-center gap-3">
        <Switch :model-value="autoMode" @update:model-value="autoMode = $event" />
        <Label>{{ autoMode ? '自动模式' : '手动模式 (每步确认)' }}</Label>
      </CardContent>
    </Card>

    <Card>
      <CardHeader><CardTitle>题目 / 授权范围</CardTitle></CardHeader>
      <CardContent class="space-y-3">
        <Textarea
          v-model="problem"
          :placeholder="mode === 'ctf' ? '粘贴 CTF 题目描述...' : '粘贴授权测试范围 (IP/域名/允许的测试类型)...'"
          class="min-h-[200px] font-mono text-sm"
        />
        <div v-if="error" class="text-destructive text-sm">{{ error }}</div>
        <Button @click="submit" :disabled="submitting" class="w-full">
          {{ submitting ? '提交中...' : '开始执行' }}
        </Button>
      </CardContent>
    </Card>
  </div>
</template>
