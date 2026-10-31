<script setup lang="ts">
/**
 * ECharts 薄封装：负责实例生命周期、主题联动、容器尺寸变化与空数据兜底。
 *
 * 只按需注册用到的图表与组件，避免把整个 echarts（约 1 MB）打进首屏包。
 * 新增图表类型时记得在这里补注册。
 */
import { onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TitleComponent,
  TooltipComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useAppStore } from '@/stores/app'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TitleComponent,
  TooltipComponent,
  CanvasRenderer
])

const props = defineProps<{
  option: echarts.EChartsCoreOption
  height?: number
  /** 是否无数据 */
  empty?: boolean
  emptyText?: string
}>()

const el = ref<HTMLDivElement | null>(null)
const chart = shallowRef<echarts.ECharts | null>(null)
const store = useAppStore()
let ro: ResizeObserver | null = null

function render() {
  if (!chart.value || props.empty) return
  chart.value.setOption(props.option, true)
}

function mount() {
  if (!el.value) return
  chart.value = echarts.init(el.value, undefined, { renderer: 'canvas' })
  render()
}

onMounted(() => {
  if (!el.value) return
  mount()
  ro = new ResizeObserver(() => chart.value?.resize())
  ro.observe(el.value)
})

onUnmounted(() => {
  ro?.disconnect()
  chart.value?.dispose()
  chart.value = null
})

watch(() => props.option, render, { deep: true })
watch(() => props.empty, (e) => { if (!e) render() })
watch(
  () => store.theme,
  () => {
    // 主题切换后重新初始化，让文字/轴线颜色跟着变
    chart.value?.dispose()
    mount()
  }
)
</script>

<template>
  <div class="chart" :style="{ height: (height ?? 260) + 'px' }">
    <div ref="el" class="chart__canvas" />
    <p v-if="empty" class="chart__empty">{{ emptyText ?? '暂无数据' }}</p>
  </div>
</template>

<style scoped>
.chart { position: relative; width: 100%; }
.chart__canvas { width: 100%; height: 100%; }
.chart__empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-size: var(--fs-sm);
  color: var(--fg-2);
  background: var(--bg-1);
}
</style>
