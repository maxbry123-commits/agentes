<template>
  <div class="task-plan-viewer">
    <!-- 计划概览 -->
    <div v-if="plan" class="plan-overview">
      <div class="plan-header">
        <h3>📋 任务计划</h3>
        <div class="plan-stats">
          <span class="stat-item">
            <span class="stat-label">总任务:</span>
            <span class="stat-value">{{ plan.total_tasks }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">已完成:</span>
            <span class="stat-value" style="color: #67c23a">{{ completedTasksCount }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">预估轮数:</span>
            <span class="stat-value">{{ plan.total_estimated_rounds }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">当前阶段:</span>
            <span class="stat-value phase">{{ getPhaseLabel(plan.current_phase) }}</span>
          </span>
        </div>
        <!-- 🔥 添加隐藏已完成任务的切换 -->
        <div class="filter-controls">
          <el-switch 
            v-model="hideCompleted" 
            active-text="隐藏已完成任务" 
            inactive-text="显示全部"
            style="--el-switch-on-color: #13ce66; --el-switch-off-color: #909399"
          />
        </div>
      </div>

      <!-- 阶段进度条 -->
      <div v-if="plan.phases && plan.phases.length > 0" class="phases-progress">
        <div 
          v-for="(phase, index) in plan.phases" 
          :key="phase"
          class="phase-item"
          :class="{ 
            active: phase === plan.current_phase,
            completed: isPhaseCompleted(phase)
          }"
        >
          <div class="phase-dot"></div>
          <div class="phase-name">{{ getPhaseLabel(phase) }}</div>
          <div v-if="index < plan.phases.length - 1" class="phase-connector"></div>
        </div>
      </div>

      <!-- 任务列表 -->
      <div v-if="filteredTasks.length > 0" class="tasks-list">
        <div 
          v-for="task in filteredTasks" 
          :key="task.id"
          class="task-card"
          :class="[
            `status-${task.status || 'pending'}`,
            `priority-${task.priority || 'medium'}`
          ]"
        >
          <div class="task-header">
            <div class="task-title">
              <span class="task-status-icon">{{ getStatusIcon(task.status) }}</span>
              <span class="task-name">{{ task.name }}</span>
              <span v-if="task.priority" class="task-priority" :class="`priority-${task.priority}`">
                {{ task.priority.toUpperCase() }}
              </span>
            </div>
            <div class="task-meta">
              <span class="task-phase">{{ getPhaseLabel(task.phase) }}</span>
              <span class="task-rounds">
                {{ task.actual_rounds || 0 }}/{{ task.estimated_rounds || 0 }} 轮
              </span>
            </div>
          </div>

          <div class="task-description">
            {{ task.description }}
          </div>

          <!-- 依赖关系 -->
          <div v-if="task.dependencies && task.dependencies.length > 0" class="task-dependencies">
            <span class="dep-label">依赖:</span>
            <span 
              v-for="depId in task.dependencies" 
              :key="depId"
              class="dep-task"
            >
              {{ getTaskName(depId) }}
            </span>
          </div>

          <!-- 进度条 -->
          <div v-if="task.status === 'in_progress'" class="task-progress">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: getTaskProgress(task) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 无计划时的提示 -->
    <div v-else class="no-plan">
      <p>暂无任务计划</p>
      <small>动态计划将在任务开始后生成</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Task {
  id: string
  name: string
  description: string
  phase: string
  priority: string
  status: string
  dependencies: string[]
  estimated_rounds: number
  actual_rounds: number
}

interface TaskPlan {
  id: string
  target_url: string
  mode: string
  phases: string[]
  current_phase: string
  total_tasks: number
  total_estimated_rounds: number
  tasks: Task[]
}

const props = defineProps<{
  plan: TaskPlan | null
}>()

// 🔥 隐藏已完成任务的状态
const hideCompleted = ref(true)  // 🔥 默认隐藏已完成任务

// 🔥 过滤后的任务列表
const filteredTasks = computed(() => {
  if (!props.plan || !props.plan.tasks) return []
  
  if (hideCompleted.value) {
    // 隐藏 completed 和 skipped 任务
    return props.plan.tasks.filter(t => 
      t.status !== 'completed' && t.status !== 'skipped'
    )
  }
  
  return props.plan.tasks
})

// 🔥 已完成任务数量
const completedTasksCount = computed(() => {
  if (!props.plan || !props.plan.tasks) return 0
  return props.plan.tasks.filter(t => 
    t.status === 'completed' || t.status === 'skipped'
  ).length
})

// 阶段标签映射
const phaseLabels: Record<string, string> = {
  reconnaissance: '侦查',
  exploitation: '利用',
  post_exploitation: '后渗透'
}

function getPhaseLabel(phase: string): string {
  return phaseLabels[phase] || phase
}

// 状态图标
function getStatusIcon(status: string): string {
  const icons: Record<string, string> = {
    pending: '⏳',
    ready: '✅',
    in_progress: '🔄',
    completed: '✔️',
    failed: '❌',
    skipped: '⏭️',
    blocked: '🚫'
  }
  return icons[status] || '❓'
}

// 判断阶段是否完成
function isPhaseCompleted(phase: string): boolean {
  if (!props.plan || !props.plan.tasks) return false
  
  const phaseTasks = props.plan.tasks.filter(t => t.phase === phase)
  if (phaseTasks.length === 0) return false
  
  return phaseTasks.every(t => t.status === 'completed' || t.status === 'skipped')
}

// 获取任务名称
function getTaskName(taskId: string): string {
  if (!props.plan || !props.plan.tasks) return taskId
  const task = props.plan.tasks.find(t => t.id === taskId)
  return task ? task.name : taskId
}

// 计算任务进度
function getTaskProgress(task: Task): number {
  if (!task.estimated_rounds || task.estimated_rounds === 0) return 0
  const actual = task.actual_rounds || 0
  return Math.min(100, (actual / task.estimated_rounds) * 100)
}
</script>

<style scoped>
.task-plan-viewer {
  background: rgba(30, 30, 30, 0.8);
  border-radius: 8px;
  padding: 16px;
  color: #e0e0e0;
  overflow: hidden;
}

.plan-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.plan-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(76, 175, 80, 0.3);
}

.plan-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #4CAF50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}

.stat-label {
  font-size: 0.7rem;
  color: #999;
  margin-bottom: 4px;
  white-space: nowrap;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: bold;
  color: #4CAF50;
  white-space: nowrap;
}

.stat-value.phase {
  color: #2196F3;
  text-transform: capitalize;
  font-size: 0.95rem;
}

/* 阶段进度条 */
.phases-progress {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  position: relative;
  overflow-x: auto;
  min-height: 60px;
}

.phase-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
  min-width: 80px;
}

.phase-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #444;
  border: 3px solid #666;
  z-index: 2;
  transition: all 0.3s;
  flex-shrink: 0;
}

.phase-item.active .phase-dot {
  background: #2196F3;
  border-color: #2196F3;
  box-shadow: 0 0 10px #2196F3;
}

.phase-item.completed .phase-dot {
  background: #4CAF50;
  border-color: #4CAF50;
}

.phase-name {
  margin-top: 6px;
  font-size: 0.75rem;
  color: #999;
  white-space: nowrap;
  text-align: center;
}

.phase-item.active .phase-name {
  color: #2196F3;
  font-weight: bold;
}

.phase-item.completed .phase-name {
  color: #4CAF50;
}

.phase-connector {
  position: absolute;
  top: 10px;
  left: 50%;
  width: 100%;
  height: 3px;
  background: #444;
  z-index: 1;
}

.phase-item.completed .phase-connector {
  background: #4CAF50;
}

/* 任务列表 */
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}

.tasks-list::-webkit-scrollbar {
  width: 6px;
}

.tasks-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.tasks-list::-webkit-scrollbar-thumb {
  background: rgba(76, 175, 80, 0.3);
  border-radius: 3px;
}

.task-card {
  background: rgba(42, 42, 42, 0.8);
  border-radius: 6px;
  padding: 12px;
  border-left: 4px solid #666;
  transition: all 0.3s;
}

.task-card:hover {
  background: rgba(42, 42, 42, 1);
  transform: translateX(2px);
}

.task-card.status-in_progress {
  border-left-color: #2196F3;
  background: rgba(42, 52, 64, 0.8);
}

.task-card.status-completed {
  border-left-color: #4CAF50;
  opacity: 0.7;
}

.task-card.status-failed {
  border-left-color: #f44336;
}

.task-card.priority-critical {
  box-shadow: 0 0 8px rgba(244, 67, 54, 0.3);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
  gap: 8px;
  flex-wrap: wrap;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.task-status-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.task-name {
  font-weight: 600;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.task-priority {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: bold;
  white-space: nowrap;
  flex-shrink: 0;
}

.task-priority.priority-critical {
  background: #f44336;
  color: white;
}

.task-priority.priority-high {
  background: #ff9800;
  color: white;
}

.task-priority.priority-medium {
  background: #2196F3;
  color: white;
}

.task-priority.priority-low {
  background: #666;
  color: white;
}

.task-meta {
  display: flex;
  gap: 10px;
  font-size: 0.75rem;
  color: #999;
  flex-wrap: wrap;
}

.task-description {
  font-size: 0.85rem;
  color: #ccc;
  margin-bottom: 8px;
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.task-dependencies {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #999;
  margin-top: 8px;
  flex-wrap: wrap;
}

.dep-label {
  font-weight: 600;
  flex-shrink: 0;
}

.dep-task {
  background: #333;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  white-space: nowrap;
}

.task-progress {
  margin-top: 10px;
}

.progress-bar {
  width: 100%;
  height: 5px;
  background: #444;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2196F3, #4CAF50);
  transition: width 0.3s ease;
}

/* 无计划提示 */
.no-plan {
  text-align: center;
  padding: 32px;
  color: #999;
}

.no-plan p {
  margin: 0 0 8px 0;
  font-size: 1rem;
}

.no-plan small {
  font-size: 0.85rem;
  color: #666;
}

.filter-controls {
  margin-top: 8px;
}
</style>
