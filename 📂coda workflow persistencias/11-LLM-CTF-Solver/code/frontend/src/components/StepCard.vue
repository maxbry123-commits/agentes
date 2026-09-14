<script setup lang="ts">
import type { SolveStepMessage } from '@/utils/interface'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

defineProps<{ step: SolveStepMessage; expanded?: boolean }>()
</script>

<template>
  <Card class="overflow-hidden">
    <CardContent class="p-4 space-y-3">
      <!-- Think -->
      <div>
        <span class="text-xs font-semibold text-muted-foreground">思考</span>
        <div class="text-sm mt-1 whitespace-pre-wrap">{{ step.think || '(无)' }}</div>
      </div>

      <!-- Tool Calls -->
      <div v-if="step.tool_calls.length">
        <span class="text-xs font-semibold text-muted-foreground">工具调用</span>
        <div class="space-y-1 mt-1">
          <div v-for="(tc, i) in step.tool_calls" :key="i"
               class="bg-muted rounded p-2 text-xs font-mono">
            <span class="text-primary">{{ tc.tool_name }}</span>
            <span v-if="tc.arguments">({{ JSON.stringify(tc.arguments).slice(0, 120) }})</span>
          </div>
        </div>
      </div>

      <!-- Output -->
      <div>
        <span class="text-xs font-semibold text-muted-foreground">输出</span>
        <pre class="text-xs mt-1 bg-muted rounded p-2 overflow-auto max-h-60">{{ step.output || '(无)' }}</pre>
      </div>

      <!-- Analysis -->
      <div v-if="step.analysis">
        <span class="text-xs font-semibold text-muted-foreground">分析</span>
        <div class="text-sm mt-1">{{ step.analysis }}</div>
      </div>

      <!-- Vulnerability (pentest) -->
      <div v-if="step.vulnerability && (step.vulnerability as any).type" class="border border-yellow-500/30 rounded p-2">
        <span class="text-xs font-semibold text-yellow-400">漏洞发现</span>
        <div class="text-xs mt-1 space-y-0.5">
          <div>类型: {{ (step.vulnerability as any).type }}</div>
          <div>严重度: {{ (step.vulnerability as any).severity }}</div>
          <div>置信度: {{ (step.vulnerability as any).confidence }}</div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
