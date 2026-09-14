<template>
  <div class="h-64">
    <v-chart :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

interface Props {
  data: {
    labels: string[]
    scans: number[]
    vulns: number[]
  }
}

const props = defineProps<Props>()

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#161619',
    borderColor: '#36363d',
    textStyle: {
      color: '#fff',
    },
  },
  legend: {
    data: ['扫描任务', '发现漏洞'],
    textStyle: {
      color: 'rgba(255, 255, 255, 0.6)',
    },
    top: 0,
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '15%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: props.data.labels,
    axisLine: {
      lineStyle: {
        color: '#36363d',
      },
    },
    axisLabel: {
      color: 'rgba(255, 255, 255, 0.6)',
    },
  },
  yAxis: {
    type: 'value',
    axisLine: {
      lineStyle: {
        color: '#36363d',
      },
    },
    axisLabel: {
      color: 'rgba(255, 255, 255, 0.6)',
    },
    splitLine: {
      lineStyle: {
        color: '#36363d',
      },
    },
  },
  series: [
    {
      name: '扫描任务',
      type: 'line',
      smooth: true,
      data: props.data.scans,
      lineStyle: {
        color: '#00d4ff',
        width: 2,
      },
      itemStyle: {
        color: '#00d4ff',
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0, 212, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 212, 255, 0)' },
          ],
        },
      },
    },
    {
      name: '发现漏洞',
      type: 'line',
      smooth: true,
      data: props.data.vulns,
      lineStyle: {
        color: '#ef4444',
        width: 2,
      },
      itemStyle: {
        color: '#ef4444',
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0)' },
          ],
        },
      },
    },
  ],
}))
</script>
