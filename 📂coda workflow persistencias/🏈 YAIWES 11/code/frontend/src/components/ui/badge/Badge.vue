<script setup lang="ts">
import { type HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { badgeVariants, type BadgeProps } from '.'

withDefaults(defineProps<{ variant?: BadgeProps['variant']; class?: HTMLAttributes['class'] }>(), {
  variant: 'default',
})
</script>

<template>
  <div :class="cn(badgeVariants({ variant }), $props.class)">
    <slot />
  </div>
</template>
