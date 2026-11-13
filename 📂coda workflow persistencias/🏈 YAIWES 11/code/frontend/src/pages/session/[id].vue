<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useTaskStore } from '@/stores/task'
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import SolveTimeline from '@/components/SolveTimeline.vue'
import StepCard from '@/components/StepCard.vue'
import FlagBanner from '@/components/FlagBanner.vue'
import PhaseIndicator from '@/components/PhaseIndicator.vue'
import TokenUsageBar from '@/components/TokenUsageBar.vue'
import ApprovalDialog from '@/components/ApprovalDialog.vue'
import type { ApprovalMessage, SolveStepMessage } from '@/utils/interface'

const props = defineProps<{ taskId: string }>()
const store = useTaskStore()

const currentApproval = ref<ApprovalMessage | null>(null)
const selectedStep = ref<SolveStepMessage | null>(null)

onMounted(async () => {
  await store.loadTaskMessages(props.taskId)
  store.connectWebSocket(props.taskId)
  store.approvalCallback = (msg: ApprovalMessage) => {
    currentApproval.value = msg
  }
})

onBeforeUnmount(() => {
  store.approvalCallback = null
  store.closeWebSocket()
})

function handleApprovalDecision(checkpointId: string, decision: Record<string, unknown>) {
  store.sendDecision(checkpointId, decision)
  currentApproval.value = null
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Top Bar -->
    <div class="flex items-center justify-between px-4 py-2 border-b">
      <div class="flex items-center gap-3">
        <span class="text-sm text-muted-foreground font-mono">{{ taskId }}</span>
        <PhaseIndicator :phase="store.latestStep?.phase ?? 'recon'" />
      </div>
      <div class="flex items-center gap-4">
        <TokenUsageBar :stats="store.latestStep?.token_stats" />
        <div class="flex items-center gap-2">
          <div :class="['h-2 w-2 rounded-full', store.wsConnected ? 'bg-green-500' : 'bg-red-500']" />
          <span class="text-xs text-muted-foreground">{{ store.wsConnected ? '已连接' : '断开' }}</span>
        </div>
        <span class="text-sm text-muted-foreground">{{ store.solveSteps.length }} 步</span>
      </div>
    </div>

    <!-- Flag Banner -->
    <FlagBanner v-if="store.flagFound" :flag="store.flagValue" />

    <!-- Main Content -->
    <ResizablePanelGroup direction="horizontal" class="flex-1">
      <ResizablePanel :default-size="35" :min-size="25">
        <SolveTimeline :steps="store.solveSteps" :selected-id="selectedStep?.id" @select="selectedStep = $event" />
      </ResizablePanel>
      <ResizableHandle />
      <ResizablePanel :default-size="65">
        <Tabs default-value="output" class="h-full flex flex-col">
          <TabsList class="mx-2 mt-2">
            <TabsTrigger value="output">输出</TabsTrigger>
            <TabsTrigger value="system">系统消息</TabsTrigger>
            <TabsTrigger value="detail">步骤详情</TabsTrigger>
          </TabsList>
          <TabsContent value="output" class="flex-1 overflow-auto p-4">
            <div v-if="store.latestStep" class="space-y-4">
              <StepCard :step="store.latestStep" :expanded="true" />
            </div>
            <div v-else class="text-center text-muted-foreground py-20">
              等待 Agent 执行...
            </div>
          </TabsContent>
          <TabsContent value="system" class="flex-1 overflow-auto p-4 space-y-1">
            <div v-for="m in store.systemMessages" :key="m.id"
                 :class="['text-xs px-3 py-1 rounded-full inline-block',
                   m.type === 'error' ? 'bg-red-500/10 text-red-400' :
                   m.type === 'success' ? 'bg-green-500/10 text-green-400' :
                   m.type === 'warning' ? 'bg-yellow-500/10 text-yellow-400' :
                   'bg-muted text-muted-foreground']">
              {{ m.content }}
            </div>
          </TabsContent>
          <TabsContent value="detail" class="flex-1 overflow-auto p-4">
            <StepCard v-if="selectedStep" :step="selectedStep" :expanded="true" />
            <p v-else class="text-muted-foreground text-sm">从左侧时间线选择一个步骤查看详情</p>
          </TabsContent>
        </Tabs>
      </ResizablePanel>
    </ResizablePanelGroup>

    <!-- HIL Approval Dialog -->
    <ApprovalDialog
      :approval="currentApproval"
      @decide="handleApprovalDecision"
      @close="currentApproval = null"
    />
  </div>
</template>
