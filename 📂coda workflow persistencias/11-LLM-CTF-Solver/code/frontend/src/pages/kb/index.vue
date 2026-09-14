<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/request'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import {
  Search, Plus, Trash2, Database, Loader2, RefreshCw, X,
} from 'lucide-vue-next'

// ── List State ──
const stats = ref({ total: 0, collection: '', sample_tags: [] as string[] })
const items = ref<any[]>([])
const selected = ref<Set<string>>(new Set())
const deleteMode = ref(false)
const loading = ref(false)
const message = ref('')

// ── Detail Dialog ──
const detailOpen = ref(false)
const detailItem = ref<any>(null)
const editContent = ref('')
const editTags = ref('')
const saving = ref(false)

// ── Search / Add ──
const searchResults = ref<any[]>([])
const searchQuery = ref('')
const newContent = ref('')
const newTags = ref('')

// ── Load ──
async function loadAll() {
  loading.value = true
  const { data } = await api.get('/kb/list')
  items.value = data.items || []
  loading.value = false
}
async function loadStats() {
  const { data } = await api.get('/kb/stats')
  stats.value = data
}
onMounted(async () => { await loadStats(); await loadAll() })

// ── Detail & Edit ──
function openDetail(item: any) {
  if (deleteMode.value) { toggleSelect(item.id); return }
  detailItem.value = item
  editContent.value = item.content || ''
  editTags.value = item.tags || ''
  detailOpen.value = true
}
async function saveDetail() {
  saving.value = true
  try {
    await api.put(`/kb/${detailItem.value.id}`, {
      content: editContent.value,
      tags: editTags.value.split(/[,，]/).map((t: string) => t.trim()).filter(Boolean),
    })
    detailOpen.value = false
    message.value = '保存成功'
    await loadStats(); await loadAll()
    setTimeout(() => message.value = '', 2000)
  } catch { /* ignore */ }
  saving.value = false
}

// ── Delete Mode ──
function toggleDeleteMode() {
  deleteMode.value = !deleteMode.value
  if (!deleteMode.value) selected.value.clear()
}
function toggleSelect(id: string) {
  if (!deleteMode.value) { openDetail(items.value.find(i => i.id === id)); return }
  if (selected.value.has(id)) selected.value.delete(id)
  else selected.value.add(id)
}
async function doDelete() {
  if (selected.value.size === 0) return
  const ids = Array.from(selected.value)
  await api.post('/kb/delete', { ids })
  selected.value.clear()
  deleteMode.value = false
  message.value = `已删除 ${ids.length} 条`
  await loadStats(); await loadAll()
  setTimeout(() => message.value = '', 2000)
}

// ── Search / Add ──
async function doSearch() {
  if (!searchQuery.value.trim()) return
  loading.value = true
  const { data } = await api.post('/kb/search', { query: searchQuery.value, n_results: 30 })
  searchResults.value = data.results || []
  loading.value = false
}
async function doAdd() {
  if (!newContent.value.trim()) return
  await api.post('/kb/add', {
    content: newContent.value,
    tags: newTags.value.split(/[,，]/).map((t: string) => t.trim()).filter(Boolean),
  })
  newContent.value = ''; newTags.value = ''
  message.value = '添加成功'
  await loadStats(); await loadAll()
  setTimeout(() => message.value = '', 2000)
}
async function doReset() {
  if (!confirm('确认清空并重建知识库？此操作不可撤销。')) return
  await api.post('/kb/reset')
  message.value = '知识库已重建'
  await loadStats(); await loadAll()
}
</script>

<template>
  <div class="p-6 mx-auto space-y-4" style="max-width: 78rem">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">知识库管理</h1>
      <div class="flex items-center gap-2">
        <span v-if="message" class="text-sm text-green-600">{{ message }}</span>
        <Badge variant="secondary" class="gap-1">
          <Database class="h-3 w-3" /> {{ stats.total }} 条
        </Badge>
        <Button variant="ghost" size="icon" @click="() => { loadStats(); loadAll() }" :disabled="loading">
          <RefreshCw :class="['h-4 w-4', loading && 'animate-spin']" />
        </Button>
      </div>
    </div>

    <Tabs default-value="list">
      <TabsList>
        <TabsTrigger value="list">浏览</TabsTrigger>
        <TabsTrigger value="search">搜索</TabsTrigger>
        <TabsTrigger value="add">添加</TabsTrigger>
        <TabsTrigger value="danger">维护</TabsTrigger>
      </TabsList>

      <!-- 浏览列表 -->
      <TabsContent value="list" class="space-y-2">
        <div class="flex gap-2">
          <Button
            :variant="deleteMode ? 'default' : 'outline'"
            size="sm"
            @click="toggleDeleteMode"
          >
            <Trash2 class="h-3 w-3 mr-1" />
            {{ deleteMode ? '取消' : '删除' }}
          </Button>
          <Button
            v-if="deleteMode"
            variant="destructive" size="sm"
            @click="doDelete" :disabled="selected.size === 0"
          >
            删除选中 ({{ selected.size }})
          </Button>
        </div>
        <ScrollArea class="h-[600px] rounded border">
          <div v-if="loading" class="p-8 text-center text-muted-foreground">
            <Loader2 class="h-5 w-5 mx-auto animate-spin" />
          </div>
          <div v-for="item in items" :key="item.id"
               :class="[
                 'px-3 py-2 border-b text-sm cursor-pointer hover:bg-muted/50 transition-colors',
                 selected.has(item.id) ? 'bg-primary/10' : '',
                 deleteMode ? '' : 'hover:bg-muted/50'
               ]"
               @click="toggleSelect(item.id)">
            <div class="flex items-start gap-2">
              <!-- Checkbox in delete mode -->
              <div v-if="deleteMode"
                   :class="['mt-1 h-4 w-4 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors',
                            selected.has(item.id) ? 'bg-primary border-primary' : 'border-gray-300']">
                <div v-if="selected.has(item.id)" class="h-2 w-2 rounded-full bg-white" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="line-clamp-2">{{ item.content }}</div>
                <div class="flex gap-1 mt-1 flex-wrap">
                  <Badge v-if="item.type" variant="secondary" class="text-[10px]">{{ item.type }}</Badge>
                  <Badge v-for="t in (item.tags || '').split(',').filter(Boolean)" :key="t" variant="outline" class="text-[10px]">{{ t }}</Badge>
                </div>
              </div>
              <div class="text-[10px] text-muted-foreground shrink-0">{{ item.id?.slice(0, 8) }}</div>
            </div>
          </div>
        </ScrollArea>
      </TabsContent>

      <!-- 搜索 -->
      <TabsContent value="search" class="space-y-3">
        <div class="flex gap-2">
          <Input v-model="searchQuery" placeholder="输入关键词搜索..." @keyup.enter="doSearch" />
          <Button @click="doSearch" :disabled="loading"><Search class="h-4 w-4 mr-1" /> 搜索</Button>
        </div>
        <div v-if="searchResults.length" class="space-y-2">
          <div v-for="(r, i) in searchResults" :key="i" class="bg-muted rounded p-3 text-sm">
            <div class="flex items-center justify-between mb-1">
              <Badge variant="secondary" class="text-[10px]">{{ r.type || 'general' }}</Badge>
              <span v-if="r.score != null" class="text-[10px] text-muted-foreground">{{ r.score }}</span>
            </div>
            <div class="whitespace-pre-wrap">{{ r.content }}</div>
          </div>
        </div>
      </TabsContent>

      <!-- 添加 -->
      <TabsContent value="add" class="space-y-3">
        <Textarea v-model="newContent" placeholder="粘贴知识内容..." class="min-h-[200px]" />
        <Input v-model="newTags" placeholder="标签，逗号分隔" />
        <Button @click="doAdd" :disabled="!newContent.trim()"><Plus class="h-4 w-4 mr-1" /> 添加到知识库</Button>
      </TabsContent>

      <!-- 维护 -->
      <TabsContent value="danger" class="space-y-3">
        <Card class="border-destructive/30">
          <CardHeader><CardTitle class="text-sm text-destructive">危险操作</CardTitle></CardHeader>
          <CardContent>
            <p class="text-xs text-muted-foreground mb-3">清空知识库并使用种子数据重建。</p>
            <Button variant="destructive" size="sm" @click="doReset">重建知识库</Button>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>

    <!-- Detail / Edit Dialog -->
    <Dialog :open="detailOpen" @update:open="detailOpen = $event">
      <DialogContent class="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle class="text-sm flex items-center justify-between">
            <span>知识详情</span>
            <Badge variant="secondary" class="text-[10px]">{{ detailItem?.type || 'general' }}</Badge>
          </DialogTitle>
        </DialogHeader>
        <div class="flex-1 overflow-auto space-y-3 py-2">
          <div>
            <label class="text-xs font-medium text-muted-foreground">内容</label>
            <Textarea v-model="editContent" class="min-h-[200px] mt-1 text-sm" />
          </div>
          <div>
            <label class="text-xs font-medium text-muted-foreground">标签（逗号分隔）</label>
            <Input v-model="editTags" class="mt-1" placeholder="web, sqli, 自动学习" />
          </div>
        </div>
        <DialogFooter class="gap-2">
          <Button variant="outline" size="sm" @click="detailOpen = false">
            <X class="h-3 w-3 mr-1" /> 取消
          </Button>
          <Button size="sm" @click="saveDetail" :disabled="saving">
            {{ saving ? '保存中...' : '确定' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
