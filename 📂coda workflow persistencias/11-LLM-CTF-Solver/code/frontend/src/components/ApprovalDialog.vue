<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import type { ApprovalMessage } from '@/utils/interface'

const props = defineProps<{ approval: ApprovalMessage | null }>()
const emit = defineEmits<{
  decide: [checkpointId: string, decision: Record<string, unknown>]
  close: []
}>()

const textInput = ref('')
const remaining = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const isOpen = computed(() => props.approval !== null)

watch(() => props.approval, (val) => {
  textInput.value = ''
  if (val) {
    remaining.value = val.timeout
    startTimer()
  } else {
    stopTimer()
  }
})

function startTimer() {
  stopTimer()
  timer = setInterval(() => {
    remaining.value -= 1
    if (remaining.value <= 0) {
      stopTimer()
    }
  }, 1000)
}

function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onUnmounted(stopTimer)

function handleConfirm(yes: boolean) {
  if (!props.approval) return
  const options = props.approval.options
  const action = yes ? (options[0] || 'y') : (options[1] || 'n')
  emit('decide', props.approval.checkpoint_id, { action, content: '' })
}

function handleChoose(option: string) {
  if (!props.approval) return
  emit('decide', props.approval.checkpoint_id, { action: option, content: '' })
}

function handlePromptSubmit() {
  if (!props.approval || !textInput.value.trim()) return
  emit('decide', props.approval.checkpoint_id, { action: '', content: textInput.value })
}

function handleClose() {
  stopTimer()
  emit('close')
}
</script>

<template>
  <Dialog :open="isOpen" @update:open="(v: boolean) => { if (!v) handleClose() }">
    <DialogContent class="sm:max-w-md" :close-on-pointer-escape="false">
      <DialogHeader>
        <DialogTitle>需要人工确认</DialogTitle>
        <DialogDescription class="whitespace-pre-wrap">{{ approval?.prompt.message }}</DialogDescription>
      </DialogHeader>

      <!-- confirm type -->
      <div v-if="approval?.prompt.type === 'confirm'" class="flex gap-2 justify-end pt-2">
        <Button variant="outline" @click="handleConfirm(false)">
          {{ approval.options[1] || 'n' }}
        </Button>
        <Button @click="handleConfirm(true)">
          {{ approval.options[0] || 'y' }}
        </Button>
      </div>

      <!-- choose type -->
      <div v-else-if="approval?.prompt.type === 'choose'" class="flex flex-col gap-2 pt-2">
        <Button v-for="opt in approval.options" :key="opt" variant="outline" @click="handleChoose(opt)">
          {{ opt }}
        </Button>
      </div>

      <!-- prompt_text type -->
      <div v-else-if="approval?.prompt.type === 'prompt_text'" class="space-y-2 pt-2">
        <Textarea v-model="textInput" placeholder="请输入..." rows="3" @keydown.ctrl.enter="handlePromptSubmit" />
        <div class="flex justify-end">
          <Button :disabled="!textInput.trim()" @click="handlePromptSubmit">提交</Button>
        </div>
      </div>

      <DialogFooter>
        <span class="text-xs text-muted-foreground">
          超时倒计时: {{ remaining }}s
        </span>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
