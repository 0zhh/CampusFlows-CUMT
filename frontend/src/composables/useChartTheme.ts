import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

/** ECharts 统一主题：轴线、文字、tooltip 跟深浅色联动 */
export function useChartTheme() {
  const store = useAppStore()

  const t = computed(() => {
    const dark = store.theme === 'dark'
    return {
      axis: dark ? '#35414f' : '#c2cad4',
      split: dark ? '#1d2530' : '#e8ecf1',
      text: dark ? '#9aa7b6' : '#4d5865',
      textStrong: dark ? '#e9eef4' : '#10151c',
      bg: dark ? '#10151c' : '#ffffff',
      border: dark ? '#35414f' : '#dde3ea',
      series: ['#e8a33d', '#3ec9a7', '#5b9bd5', '#c05c8e', '#6e7fd4', '#e2605a']
    }
  })

  const tooltip = computed(() => ({
    backgroundColor: t.value.bg,
    borderColor: t.value.border,
    borderWidth: 1,
    padding: [8, 11],
    textStyle: { color: t.value.textStrong, fontSize: 12 },
    extraCssText: 'box-shadow: 0 8px 24px rgb(0 0 0 / 0.35); border-radius: 8px;'
  }))

  const axisCommon = computed(() => ({
    axisLine: { lineStyle: { color: t.value.axis } },
    axisTick: { show: false },
    axisLabel: { color: t.value.text, fontSize: 11 },
    splitLine: { lineStyle: { color: t.value.split, type: 'dashed' as const } }
  }))

  return { t, tooltip, axisCommon }
}
