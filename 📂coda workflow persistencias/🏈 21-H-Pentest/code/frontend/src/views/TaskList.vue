<template>
  <div class="task-list-page">
    <el-page-header @back="$router.push('/')">
      <template #content>
        <span class="page-title">任务管理</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="main-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>任务列表 (当前显示 {{ tasks.length }} / 总共 {{ allTasks.length }})</span>
          <el-switch 
            v-model="showCompleted" 
            active-text="显示全部" 
            inactive-text="智能过滤"
          />
        </div>
      </template>
      <el-table :data="tasks" stripe>
        <el-table-column prop="id" label="任务ID" width="120">
          <template #default="{ row }">
            {{ row.id.slice(0, 8) }}...
          </template>
        </el-table-column>
        <el-table-column prop="target_url" label="目标URL" min-width="200" />
        <el-table-column prop="mode" label="模式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.mode === 'ctf' ? 'danger' : 'primary'">
              {{ row.mode.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="150">
          <template #default="{ row }">
            <el-progress 
              :percentage="(row.current_round / row.max_rounds) * 100"
              :format="() => `${row.current_round}/${row.max_rounds}`"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <!-- 🔥 正在运行/暂停：监控 -->
              <el-button 
                v-if="row.status === 'running' || row.status === 'paused'" 
                size="small" 
                type="primary"
                @click="$router.push(`/monitor/${row.id}`)"
              >
                监控
              </el-button>
              
              <!-- 🔥 已完成/失败：查看对话 -->
              <el-button 
                v-if="row.status === 'completed' || row.status === 'failed'" 
                size="small"
                type="success"
                @click="$router.push(`/monitor/${row.id}`)"
              >
                对话
              </el-button>
              
              <!-- 暂停按钮 -->
              <el-button 
                v-if="row.status === 'running'" 
                size="small" 
                type="warning"
                @click="pauseTask(row.id)"
              >
                暂停
              </el-button>
              
              <!-- 继续按钮 -->
              <el-button 
                v-if="row.status === 'paused'" 
                size="small" 
                type="success"
                @click="resumeTask(row.id)"
              >
                继续
              </el-button>
              
              <!-- 报告按钮 -->
              <el-button 
                v-if="row.status === 'completed'" 
                size="small"
                @click="viewReport(row.id)"
              >
                报告
              </el-button>
              
              <!-- 删除按钮 -->
              <el-button 
                v-if="row.status !== 'running'" 
                size="small" 
                type="danger"
                @click="deleteTask(row.id)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const allTasks = ref<any[]>([])  // 🔥 所有任务
const showCompleted = ref(false)  // 🔥 是否显示已完成任务

// 🔥 智能过滤：默认只显示运行中+暂停+最近3个完成/失败
const tasks = computed(() => {
  const running = allTasks.value.filter(t => t.status === 'running' || t.status === 'paused' || t.status === 'pending')
  
  if (showCompleted.value) {
    // 显示全部
    return allTasks.value
  } else {
    // 只显示运行中 + 最近3个完成/失败
    const completed = allTasks.value
      .filter(t => t.status === 'completed' || t.status === 'failed')
      .sort((a, b) => new Date(b.completed_at || b.created_at).getTime() - new Date(a.completed_at || a.created_at).getTime())
      .slice(0, 3)
    
    return [...running, ...completed].sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  }
})

const loadTasks = async () => {
  try {
    const { data } = await axios.get('http://localhost:8000/api/v1/tasks/')
    allTasks.value = data
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  }
}

const pauseTask = async (taskId: string) => {
  try {
    await axios.post(`http://localhost:8000/api/v1/tasks/${taskId}/intervention`, {
      action: 'pause'
    })
    ElMessage.success('任务已暂停')
    await loadTasks()
  } catch (error) {
    ElMessage.error('暂停任务失败')
  }
}

const resumeTask = async (taskId: string) => {
  try {
    await axios.post(`http://localhost:8000/api/v1/tasks/${taskId}/intervention`, {
      action: 'resume'
    })
    ElMessage.success('任务已恢复')
    await loadTasks()
  } catch (error) {
    ElMessage.error('恢复任务失败')
  }
}

const deleteTask = async (taskId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗?', '警告', {
      type: 'warning'
    })
    
    await axios.delete(`http://localhost:8000/api/v1/tasks/${taskId}`)
    ElMessage.success('任务已删除')
    await loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除任务失败')
    }
  }
}

const viewReport = (taskId: string) => {
  router.push(`/report/${taskId}`)
}

const getStatusType = (status: string) => {
  const map: any = {
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    paused: 'warning',
    pending: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: any = {
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停',
    pending: '等待中'
  }
  return map[status] || status
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTasks()
  const timer = setInterval(loadTasks, 3000)
  
  // 🔥 组件卸载时清理
  onUnmounted(() => {
    clearInterval(timer)
    console.log('🧹 TaskList轮询已停止')
  })
})
</script>

<style scoped>
.task-list-page {
  padding: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.main-card {
  margin-top: 20px;
}
</style>
