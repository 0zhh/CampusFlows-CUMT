/**
 * 校园配送线路的单一数据源。
 * - 两个入口：北门、东门
 * - 每条线路以 gateId + siteId 为键，值是 [lng, lat] 折线
 * - 用户描的点存在 localStorage，地图与描线面板共用同一份，画完立刻能看见
 */
import { computed, ref } from 'vue'
import bundled from '@/data/station_routes.json'
import { SITES } from '@/data/sites'

export interface Gate {
  id: string
  name: string
  lon: number
  lat: number
}

const KEY = 'campusflow-routes-v2'

const DEFAULT_GATES: Gate[] = [
  { id: 'north', name: '北门', lon: 117.144061, lat: 34.220985 },
  { id: 'east', name: '东门', lon: 117.1439, lat: 34.213488 }
]

type LineMap = Record<string, [number, number][]>

function readStored(): { gates: Gate[]; lines: LineMap } {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) {
      const o = JSON.parse(raw)
      if (o && Array.isArray(o.gates) && o.lines) return { gates: o.gates, lines: o.lines }
    }
  } catch {
    /* 忽略 */
  }
  const b = bundled as any
  return { gates: (b?.gates as Gate[]) ?? DEFAULT_GATES, lines: {} }
}

/** 旧版描线只存了"最后一条"，这里尽量救回来（默认算北门） */
function migrateOld() {
  try {
    const raw = localStorage.getItem('campusflow-trace-v1')
    if (!raw) return {}
    const o = JSON.parse(raw)
    if (Array.isArray(o?.points) && o.points.length >= 2 && o.target) {
      return { ['north:' + o.target]: o.points.map((p: any) => [p.lng, p.lat]) }
    }
  } catch {
    /* 忽略 */
  }
  return {}
}

const state = readStored()
if (!Object.keys(state.lines).length) {
  const old = migrateOld()
  if (Object.keys(old).length) state.lines = old
}
export const gates = ref<Gate[]>(state.gates)
export const lines = ref<LineMap>(state.lines)

function persist() {
  try {
    localStorage.setItem(KEY, JSON.stringify({ gates: gates.value, lines: lines.value }))
  } catch {
    /* 忽略 */
  }
}

export const routeKey = (gateId: string, siteId: string) => gateId + ':' + siteId

export function getLine(gateId: string, siteId: string): [number, number][] {
  return lines.value[routeKey(gateId, siteId)] ?? []
}

export function setLine(gateId: string, siteId: string, pts: [number, number][]) {
  const k = routeKey(gateId, siteId)
  const next = { ...lines.value }
  if (pts.length) next[k] = pts
  else delete next[k]
  lines.value = next
  persist()
}

export function setGatePos(id: string, lon: number, lat: number) {
  gates.value = gates.value.map((g) => (g.id === id ? { ...g, lon, lat } : g))
  persist()
}

export function resetAll() {
  lines.value = {}
  gates.value = DEFAULT_GATES.map((g) => ({ ...g }))
  persist()
}

/** 已画线路一览，供面板列出来 */
export const summary = computed(() => {
  const out: { gate: Gate; siteName: string; siteId: string; count: number }[] = []
  for (const g of gates.value) {
    for (const s of SITES) {
      out.push({ gate: g, siteId: s.id, siteName: s.shortName, count: getLine(g.id, s.id).length })
    }
  }
  return out
})

/** 导出成可回填给项目的 JSON */
export function exportJson() {
  const routes = Object.entries(lines.value).map(([k, pts]) => {
    const [gateId, siteId] = k.split(':')
    return { gate_id: gateId, site_id: siteId, polyline: pts.map((p) => [Number(p[0].toFixed(6)), Number(p[1].toFixed(6))]) }
  })
  return JSON.stringify({ gates: gates.value, routes }, null, 2)
}
