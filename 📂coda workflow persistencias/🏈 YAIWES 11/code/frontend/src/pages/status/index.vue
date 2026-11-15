<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/request'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { RefreshCw, Wifi, WifiOff, Check, X, Zap, Loader2, Server } from 'lucide-vue-next'

// ── LLM Test ──
const llmResults = ref<Record<string, any>>({})
const llmTesting = ref(false)
async function testLlm() {
  llmTesting.value = true
  llmResults.value = {}
  try { const { data } = await api.post('/status/llm'); llmResults.value = data.results || {} }
  catch { /* ignore */ }
  llmTesting.value = false
}

// ── Health ──
const health = ref<{ status: string; redis: boolean } | null>(null)
async function fetchHealth() {
  try { const { data } = await api.get('/health'); health.value = data }
  catch { health.value = { status: 'error', redis: false } }
}

// ── Env Probe ──
const env = ref<any>(null)
const envLoading = ref(false)
async function fetchEnv() {
  envLoading.value = true
  try { const { data } = await api.get('/status/env'); env.value = data }
  catch { /* ignore */ }
  envLoading.value = false
}
async function refreshEnv() {
  envLoading.value = true
  try { const { data } = await api.post('/status/env/refresh'); env.value = data }
  catch { /* ignore */ }
  envLoading.value = false
}

// ── MCP ──
const mcp = ref<any>(null)
async function fetchMcp() {
  try { const { data } = await api.get('/status/mcp'); mcp.value = data }
  catch { /* ignore */ }
}

onMounted(async () => { await Promise.all([fetchHealth(), fetchEnv(), fetchMcp()]) })
</script>

<template>
  <div class="p-6 max-w-3xl mx-auto space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">连接测试</h1>
      <Button variant="outline" size="sm" @click="testLlm" :disabled="llmTesting">
        <Loader2 v-if="llmTesting" class="h-4 w-4 mr-1 animate-spin" />
        <Zap v-else class="h-4 w-4 mr-1" />
        {{ llmTesting ? '测试中...' : '测试全部 LLM' }}
      </Button>
    </div>

    <!-- Health -->
    <Card>
      <CardHeader class="pb-2"><CardTitle class="text-sm">后端健康</CardTitle></CardHeader>
      <CardContent>
        <div v-if="health" class="flex items-center gap-4 text-sm">
          <Badge :variant="health.status === 'ok' ? 'default' : 'destructive'" class="gap-1">
            <Check v-if="health.status === 'ok'" class="h-3 w-3" />
            <X v-else class="h-3 w-3" />
            {{ health.status === 'ok' ? '正常' : '异常' }}
          </Badge>
          <Badge :variant="health.redis ? 'default' : 'destructive'" class="gap-1">
            <Check v-if="health.redis" class="h-3 w-3" />
            <X v-else class="h-3 w-3" />
            Redis {{ health.redis ? '已连接' : '断开' }}
          </Badge>
        </div>
        <div v-else class="text-sm text-muted-foreground">检测中...</div>
      </CardContent>
    </Card>

    <!-- LLM -->
    <Card>
      <CardHeader class="pb-2"><CardTitle class="text-sm">LLM 端点</CardTitle></CardHeader>
      <CardContent>
        <div v-if="Object.keys(llmResults).length" class="space-y-1.5">
          <div v-for="(r, name) in llmResults" :key="name"
               class="flex items-center justify-between text-sm py-1 border-b last:border-0">
            <div class="flex items-center gap-2">
              <span class="font-medium">{{ name }}</span>
              <span class="text-xs text-muted-foreground">{{ r.model }}</span>
            </div>
            <Badge v-if="r.status === 'pass'" variant="default" class="gap-1">
              <Check class="h-3 w-3" /> {{ r.elapsed_s }}s
            </Badge>
            <Badge v-else-if="r.status === 'skip'" variant="secondary">未配置</Badge>
            <Badge v-else variant="destructive" class="gap-1">
              <X class="h-3 w-3" /> {{ r.detail?.slice(0, 60) || '失败' }}
            </Badge>
          </div>
        </div>
        <div v-else class="text-sm text-muted-foreground">点击"测试全部 LLM"开始检测</div>
      </CardContent>
    </Card>

    <!-- Kali -->
    <Card>
      <CardHeader class="pb-2">
        <div class="flex items-center justify-between">
          <CardTitle class="text-sm">Kali 环境</CardTitle>
          <Button variant="ghost" size="icon" @click="refreshEnv" :disabled="envLoading">
            <RefreshCw :class="['h-3 w-3', envLoading && 'animate-spin']" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div v-if="env?.status === 'ok'" class="space-y-2 text-sm">
          <div class="flex items-center gap-2">
            <Wifi class="h-4 w-4 text-green-600" />
            <span class="text-muted-foreground">{{ (env.os_info || '').split('\n')[0]?.slice(0, 60) }}</span>
          </div>

          <details class="text-xs">
            <summary class="cursor-pointer font-medium text-muted-foreground">
              可用工具 ({{ env.tools_found?.length || 0 }})
            </summary>
            <div class="flex flex-wrap gap-1 mt-1 ml-5">
              <Badge v-for="t in env.tools_found" :key="t" variant="secondary" class="text-[10px]">{{ t }}</Badge>
            </div>
          </details>

          <details class="text-xs">
            <summary class="cursor-pointer font-medium text-muted-foreground">
              缺失工具 ({{ env.tools_missing?.length || 0 }})
            </summary>
            <div class="flex flex-wrap gap-1 mt-1 ml-5">
              <Badge v-for="t in env.tools_missing" :key="t" variant="outline" class="text-[10px]">{{ t }}</Badge>
            </div>
          </details>

          <details class="text-xs">
            <summary class="cursor-pointer font-medium text-muted-foreground">
              Python 模块 ({{ env.py_modules_found?.length || 0 }})
            </summary>
            <div class="flex flex-wrap gap-1 mt-1 ml-5">
              <Badge v-for="m in env.py_modules_found" :key="m" variant="secondary" class="text-[10px]">{{ m }}</Badge>
            </div>
          </details>

          <div class="flex gap-2">
            <Badge v-for="(v, k) in env.network || {}" :key="k"
                   :variant="v === 'OK' ? 'default' : 'destructive'" class="text-[10px]">
              网络: {{ k }} {{ v === 'OK' ? '✓' : '✗' }}
            </Badge>
          </div>
        </div>
        <div v-else class="text-sm flex items-center gap-2 text-muted-foreground">
          <WifiOff class="h-4 w-4" />
          {{ env?.detail || 'SSH 未配置，跳过环境探测' }}
        </div>
      </CardContent>
    </Card>

    <!-- MCP -->
    <Card>
      <CardHeader class="pb-2"><CardTitle class="text-sm">MCP 服务</CardTitle></CardHeader>
      <CardContent>
        <div v-if="mcp?.servers?.length" class="space-y-2 text-sm">
          <div v-for="s in mcp.servers" :key="s.name" class="flex items-center justify-between py-1 border-b last:border-0">
            <div class="flex items-center gap-2">
              <Server class="h-4 w-4 text-muted-foreground" />
              <span class="font-medium">{{ s.name }}</span>
              <span class="text-xs text-muted-foreground">{{ s.type }}</span>
            </div>
            <div class="flex items-center gap-2">
              <Badge variant="secondary" class="text-[10px]">{{ s.lazy ? '懒加载' : '自动连接' }}</Badge>
              <Badge v-if="s.auto_activate?.length" variant="outline" class="text-[10px]">
                自动: {{ s.auto_activate.join(', ') }}
              </Badge>
              <Badge :variant="s.status === 'configured' ? 'default' : 'secondary'"
                     class="text-[10px]">{{ s.status === 'configured' ? '已配置' : s.status }}</Badge>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-muted-foreground">无 MCP 服务配置</div>
      </CardContent>
    </Card>
  </div>
</template>
