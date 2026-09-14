<template>
  <div class="space-y-6">
    <!-- 新建扫描任务 -->
    <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
      <h3 class="text-lg font-semibold text-white mb-6">新建扫描任务</h3>
      
      <div class="grid grid-cols-4 gap-6">
        <div class="col-span-2">
          <t-input 
            v-model="scanConfig.target"
            placeholder="输入目标IP/域名/CIDR"
          >
            <template #prefix-icon>
              <Target class="w-4 h-4" />
            </template>
          </t-input>
        </div>

        <t-select v-model="scanConfig.scan_type" placeholder="扫描类型">
          <t-option value="quick" label="快速扫描" />
          <t-option value="full" label="完整扫描" />
          <t-option value="vuln" label="漏洞扫描" />
          <t-option value="web" label="Web扫描" />
        </t-select>

        <t-button theme="primary" block @click="startScan" :loading="scanning">
          <Play class="w-4 h-4 mr-2" />
          开始扫描
        </t-button>
      </div>

      <div class="mt-6 pt-6 border-t border-dark-500">
        <t-collapse :expand-icon-placement="'right'">
          <t-collapse-panel header="高级选项" value="advanced">
            <div class="grid grid-cols-3 gap-4 pt-4">
              <div>
                <label class="block text-sm text-gray-400 mb-2">扫描深度</label>
                <t-select v-model="scanConfig.depth">
                  <t-option value="quick" label="快速" />
                  <t-option value="normal" label="标准" />
                  <t-option value="deep" label="深度" />
                </t-select>
              </div>
              <div>
                <label class="block text-sm text-gray-400 mb-2">超时时间(秒)</label>
                <t-input-number v-model="scanConfig.timeout" :min="60" :max="3600" />
              </div>
              <div>
                <label class="block text-sm text-gray-400 mb-2">测试阶段</label>
                <t-checkbox-group v-model="scanConfig.phases">
                  <t-checkbox value="recon">信息收集</t-checkbox>
                  <t-checkbox value="vuln">漏洞分析</t-checkbox>
                  <t-checkbox value="exploit">漏洞利用</t-checkbox>
                  <t-checkbox value="report">报告生成</t-checkbox>
                </t-checkbox-group>
              </div>
            </div>
          </t-collapse-panel>
        </t-collapse>
      </div>
    </div>

    <!-- 扫描任务列表 -->
    <div class="grid grid-cols-2 gap-6">
      <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-white">进行中任务</h3>
          <t-badge :count="runningTasks.length" />
        </div>
        
        <div v-if="runningTasks.length === 0" class="text-center py-8 text-gray-400">
          暂无进行中的任务
        </div>
        
        <div v-else class="space-y-4">
          <div 
            v-for="task in runningTasks" 
            :key="task.id"
            class="p-4 rounded-lg bg-dark-700 border border-dark-500"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-cyber-blue/20 flex items-center justify-center">
                  <Radar class="w-4 h-4 text-cyber-blue animate-pulse" />
                </div>
                <div>
                  <h4 class="text-white text-sm font-medium">{{ task.target }}</h4>
                  <p class="text-xs text-gray-400">{{ task.scan_type }}</p>
                </div>
              </div>
              <t-button variant="text" size="small" theme="danger" @click="cancelTask(task.id)">
                <Square class="w-4 h-4" />
              </t-button>
            </div>
            <t-progress :percentage="task.progress" />
            <div class="mt-3 space-y-1">
              <p class="text-xs text-cyber-blue">
                {{ task.current_phase_label || '等待调度' }}
                <span v-if="task.round_index" class="text-gray-400 ml-2">
                  第 {{ task.round_index }} / {{ task.round_total || '?' }} 轮
                </span>
              </p>
              <p class="text-xs text-gray-400 break-words">
                {{ task.status_detail || getStatusText(task.status) }}
              </p>
              <p v-if="task.current_tool" class="text-[11px] text-amber-400 break-words">
                当前工具: {{ task.current_tool }}
                <span v-if="task.tool_status" class="text-gray-500 ml-1">({{ task.tool_status }})</span>
              </p>
              <p v-if="task.analysis_status" class="text-[11px] text-violet-300">
                分析状态: {{ getAnalysisText(task.analysis_status) }}
              </p>
              <div class="flex items-center justify-between text-[11px] text-gray-500">
                <span>{{ task.progress }}%</span>
                <t-button
                  v-if="task.session_id"
                  variant="text"
                  size="small"
                  @click="router.push(`/sessions/${task.session_id}`)"
                >
                  查看会话
                </t-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-white">任务队列</h3>
          <t-badge :count="pendingTasks.length" />
        </div>
        
        <div v-if="pendingTasks.length === 0" class="text-center py-8 text-gray-400">
          暂无等待中的任务
        </div>
        
        <div v-else class="space-y-3">
          <div 
            v-for="task in pendingTasks" 
            :key="task.id"
            class="flex items-center justify-between p-3 rounded-lg bg-dark-700"
          >
            <div class="flex items-center gap-3">
              <Clock class="w-4 h-4 text-gray-400" />
              <span class="text-sm text-gray-300">{{ task.target }}</span>
            </div>
            <t-button variant="text" size="small" @click="cancelTask(task.id)">取消</t-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 扫描历史 -->
    <div class="bg-dark-800 rounded-xl p-6 border border-dark-500">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-white">扫描历史</h3>
        <t-button variant="outline" size="small" @click="loadTasks">刷新</t-button>
      </div>
      
      <t-table 
        :data="completedTasks"
        :columns="historyColumns"
        row-key="id"
        hover
      >
        <template #operation="{ row }">
          <t-button variant="text" size="small" @click="viewReport(row.id)">查看报告</t-button>
        </template>
      </t-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Target, Play, Radar, Square, Clock } from 'lucide-vue-next'
import { scanApi } from '../api'

const router = useRouter()
const scanning = ref(false)
const tasks = ref<any[]>([])

const scanConfig = ref({
  target: '',
  scan_type: 'quick',
  depth: 'normal',
  timeout: 300,
  phases: ['recon', 'vuln', 'exploit', 'report'],
})

const historyColumns = [
  { colKey: 'target', title: '目标' },
  { colKey: 'scan_type', title: '类型' },
  { colKey: 'status', title: '状态' },
  { colKey: 'created_at', title: '创建时间' },
  { colKey: 'operation', title: '操作' },
]

const runningTasks = computed(() => tasks.value.filter(t => t.status === 'running'))
const pendingTasks = computed(() => tasks.value.filter(t => t.status === 'pending'))
const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed' || t.status === 'failed'))

const loadTasks = async () => {
  try {
    const data = await scanApi.listTasks() as any
    tasks.value = (data.tasks || []).map((task: any) => ({
      ...task,
      progress: typeof task.progress === 'number'
        ? task.progress
        : task.status === 'completed'
          ? 100
          : task.status === 'running'
            ? 50
            : 0,
    }))
  } catch (error) {
    console.error('加载任务失败:', error)
  }
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[status] || status
}

const getAnalysisText = (status: string) => {
  const map: Record<string, string> = {
    running: '推理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

const startScan = async () => {
  if (!scanConfig.value.target) return
  scanning.value = true
  try {
    await scanApi.start(scanConfig.value)
    scanConfig.value.target = ''
    await loadTasks()
  } catch (error) {
    console.error('启动扫描失败:', error)
  } finally {
    scanning.value = false
  }
}

const cancelTask = async (taskId: string) => {
  try {
    await scanApi.cancel(taskId)
    await loadTasks()
  } catch (error) {
    console.error('取消任务失败:', error)
  }
}

const viewReport = (taskId: string) => {
  router.push(`/reports?id=${taskId}`)
}

let refreshTimer: number | null = null

onMounted(() => {
  loadTasks()
  refreshTimer = window.setInterval(loadTasks, 10000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>
