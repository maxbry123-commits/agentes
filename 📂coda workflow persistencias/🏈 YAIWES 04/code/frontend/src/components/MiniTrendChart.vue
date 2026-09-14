<template>
  <svg viewBox="0 0 80 48" class="w-full h-full">
    <defs>
      <linearGradient :id="`gradient-${color}`" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" :stop-color="color" stop-opacity="0.3" />
        <stop offset="100%" :stop-color="color" stop-opacity="0" />
      </linearGradient>
    </defs>
    <path
      :d="areaPath"
      :fill="`url(#gradient-${color})`"
    />
    <path
      :d="linePath"
      fill="none"
      :stroke="color"
      stroke-width="2"
      stroke-linecap="round"
    />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  color: string
  points?: number[]
}

const props = defineProps<Props>()

const normalizedPoints = computed(() => {
  const source = Array.isArray(props.points) && props.points.length > 1
    ? props.points
    : [0, 0, 0, 0, 0, 0, 0]

  // Avoid division by zero while preserving the visible shape.
  const hasPositiveValue = source.some((value) => value > 0)
  return hasPositiveValue ? source : source.map((_value, index) => index + 1)
})

const linePath = computed(() => {
  const width = 80
  const height = 48
  const stepX = width / (normalizedPoints.value.length - 1)
  const maxY = Math.max(...normalizedPoints.value, 1)
  
  let path = ''
  normalizedPoints.value.forEach((y, i) => {
    const x = i * stepX
    const normalizedY = height - (y / maxY) * (height - 10)
    if (i === 0) {
      path += `M ${x} ${normalizedY}`
    } else {
      path += ` L ${x} ${normalizedY}`
    }
  })
  return path
})

const areaPath = computed(() => {
  const width = 80
  const height = 48
  const stepX = width / (normalizedPoints.value.length - 1)
  const maxY = Math.max(...normalizedPoints.value, 1)
  
  let path = `M 0 ${height}`
  normalizedPoints.value.forEach((y, i) => {
    const x = i * stepX
    const normalizedY = height - (y / maxY) * (height - 10)
    path += ` L ${x} ${normalizedY}`
  })
  path += ` L ${width} ${height} Z`
  return path
})
</script>
