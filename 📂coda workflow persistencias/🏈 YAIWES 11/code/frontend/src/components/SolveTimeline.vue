<script setup lang="ts">
import type { SolveStepMessage } from '@/utils/interface'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const props = defineProps<{ steps: SolveStepMessage[]; selectedId?: string }>()
const emit = defineEmits<{ select: [step: SolveStepMessage] }>()

const phaseLabel: Record<string, string> = { recon: '侦察', exploit: '利用', report: '报告' }
const phaseColor: Record<string, string> = {
  recon: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  exploit: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  report: 'bg-green-500/10 text-green-400 border-green-500/30',
}
</script>

<template>
  <div class="h-full overflow-auto p-2 space-y-1">
    <div class="text-xs text-muted-foreground px-2 py-1 font-medium">步骤时间线</div>
    <div v-if="steps.length === 0" class="text-center text-muted-foreground text-sm py-10">
      等待首步输出...
    </div>
    <Card v-for="step in steps" :key="step.id"
         @click="emit('select', step)"
         :class="['p-3 cursor-pointer hover:bg-muted/50 transition-colors text-sm',
                  step.flag_found ? 'border-primary flag-found' : '',
                  props.selectedId === step.id ? 'border-primary bg-primary/5' : '']">
      <div class="flex items-center justify-between mb-1">
        <span class="font-mono text-xs font-bold">#{{ String(step.step_num).padStart(2, '0') }}</span>
        <Badge :class="phaseColor[step.phase] ?? ''" variant="outline" class="text-[10px] px-1.5 py-0">
          {{ phaseLabel[step.phase] ?? step.phase }}
        </Badge>
      </div>
      <div class="text-xs text-muted-foreground truncate">{{ step.think.slice(0, 80) || '(无思考)' }}</div>
      <div v-if="step.tool_names.length" class="flex gap-1 mt-1 flex-wrap">
        <span v-for="t in step.tool_names" :key="t"
              class="text-[10px] bg-muted px-1 py-0.5 rounded">{{ t }}</span>
      </div>
      <div v-if="step.flag_found" class="text-xs text-primary mt-1 font-bold">
        FLAG: {{ step.flag_value }}
      </div>
    </Card>
  </div>
</template>
