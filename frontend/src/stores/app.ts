import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { SITE_BY_ID } from '@/data/sites'

export type Theme = 'dark' | 'light'

/** 演示数据来源：local = 内置样例；api = 后端真实接口 */
export type DataMode = 'local' | 'api'

const THEME_KEY = 'campusflow-theme'
const SITE_POS_KEY = 'campusflow-site-pos-v1'
const MANUAL_BOUNDS_KEY = 'campusflow-manual-bounds-v1'

export interface GeoBounds { west: number; south: number; east: number; north: number }

export interface LatLng { lat: number; lng: number }

/** 手册原图默认覆盖范围（未校准时）；北侧留到 34.2250 是为了把校门口也框进来 */
const DEFAULT_MANUAL_BOUNDS: GeoBounds = { west: 117.125, south: 34.204, east: 117.153, north: 34.225 }

function readManualBounds(): GeoBounds | null {
  try {
    const raw = localStorage.getItem(MANUAL_BOUNDS_KEY)
    if (!raw) return null
    const o = JSON.parse(raw)
    return typeof o?.west === 'number' ? (o as GeoBounds) : null
  } catch {
    return null
  }
}

/** 读回手工校准过的站点坐标 */
function readSitePos(): Record<string, LatLng> {
  try {
    const raw = localStorage.getItem(SITE_POS_KEY)
    if (!raw) return {}
    const o = JSON.parse(raw)
    return typeof o === 'object' && o ? o : {}
  } catch {
    return {}
  }
}

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

  /** 手册原图在地图上的覆盖范围；校准后与站点坐标一起保存，切换底图时红点仍对得上 */
  const manualBounds = ref<GeoBounds>(readManualBounds() ?? DEFAULT_MANUAL_BOUNDS)

  function setManualBounds(b: GeoBounds) {
    manualBounds.value = b
    try {
      localStorage.setItem(MANUAL_BOUNDS_KEY, JSON.stringify(b))
    } catch {
      /* 忽略 */
    }
  }

  function clearManualBounds() {
    manualBounds.value = DEFAULT_MANUAL_BOUNDS
    try {
      localStorage.removeItem(MANUAL_BOUNDS_KEY)
    } catch {
      /* 忽略 */
    }
  }

  /** 手工校准的站点坐标（为空则用 site_geolocation.json 里的默认值） */
  const siteOverride = ref<Record<string, LatLng>>(readSitePos())
  const hasOverride = computed(() => Object.keys(siteOverride.value).length > 0)

  function sitePos(id: string): LatLng {
    const o = siteOverride.value[id]
    if (o) return o
    const s = SITE_BY_ID[id]
    return { lat: s.lat, lng: s.lng }
  }

  function setSiteOverride(o: Record<string, LatLng>) {
    siteOverride.value = { ...o }
    try {
      localStorage.setItem(SITE_POS_KEY, JSON.stringify(o))
    } catch {
      /* 忽略 */
    }
  }

  function clearSiteOverride() {
    siteOverride.value = {}
    try {
      localStorage.removeItem(SITE_POS_KEY)
    } catch {
      /* 忽略 */
    }
  }

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

  return {
    theme, dataMode, scenarioId, timeCursor, playing, isDemoData,
    siteOverride: readonly(siteOverride), hasOverride, sitePos,
    setSiteOverride, clearSiteOverride, manualBounds, setManualBounds, clearManualBounds,
    setTheme, toggleTheme
  }
})
