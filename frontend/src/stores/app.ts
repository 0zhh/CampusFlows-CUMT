import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type Theme = 'dark' | 'light'

/** 演示数据来源：local = 内置样例；api = 后端真实接口 */
export type DataMode = 'local' | 'api'

const THEME_KEY = 'campusflow-theme'

/** 读回上次选择的主题；SSR 或隐私模式下取不到就用深色 */
function readTheme(): Theme {
  try {
    const v = localStorage.getItem(THEME_KEY)
    if (v === 'light' || v === 'dark') return v
  } catch {
    /* 忽略：localStorage 不可用时退回默认值 */
  }
  return 'dark'
}

export const useAppStore = defineStore('app', () => {
  const theme = ref<Theme>(readTheme())
  const dataMode = ref<DataMode>('local')
  const scenarioId = ref<string>('S2-PEAK')
  const timeCursor = ref<number>(0) // 时间桶下标
  const playing = ref<boolean>(false)

  const isDemoData = computed(() => dataMode.value === 'local')

  function setTheme(v: Theme) {
    theme.value = v
    document.documentElement.dataset.theme = v
    try {
      localStorage.setItem(THEME_KEY, v)
    } catch {
      /* 忽略：写不进去不影响当前会话 */
    }
  }

  function toggleTheme() {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  return { theme, dataMode, scenarioId, timeCursor, playing, isDemoData, setTheme, toggleTheme }
})
