<template>
  <div class="h-48">
    <v-chart :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'

use([
  CanvasRenderer,
  PieChart,
  TooltipComponent,
  LegendComponent,
])

interface VulnItem {
  name: string
  value: number
  color: string
}

interface Props {
  data: VulnItem[]
}

const props = defineProps<Props>()

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: '#161619',
    borderColor: '#36363d',
    textStyle: {
      color: '#fff',
    },
  },
  legend: {
    orient: 'vertical',
    right: 10,
    top: 'center',
    textStyle: {
      color: 'rgba(255, 255, 255, 0.6)',
    },
  },
  series: [
    {
      type: 'pie',
      radius: ['50%', '70%'],
      center: ['30%', '50%'],
      avoidLabelOverlap: false,
      label: {
        show: false,
      },
      labelLine: {
        show: false,
      },
      data: props.data.map(item => ({
        value: item.value,
        name: item.name,
        itemStyle: {
          color: item.color,
        },
      })),
    },
  ],
}))
</script>
