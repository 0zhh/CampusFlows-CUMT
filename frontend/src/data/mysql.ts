/**
 * MySQL 形态才有的五个功能接口。
 * 全部走"失败返回 null"的约定：后端没起或不是 mysql profile 时，页面回落到本地数据。
 */
const TIMEOUT_MS = 2500

async function call<T>(path: string, init?: RequestInit): Promise<T | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(path, { ...init, signal: ctrl.signal })
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

export interface PickupInfo {
  code: string
  siteId: string
  siteName?: string
  parcelId: string
  carrier: string
  size: string
  shelvedAt: string
  status: string
  shelfNo: number
  tier: number
  cell: number
  zoneId: string
}

export interface CarrierStat {
  carrierCode: string
  carrier: string
  onShelf: number
}

export interface RunRow {
  id: number
  scenarioId: string
  seed: number
  paramVersion: string
  createdAt: string
  peakI: number
  riskBuckets: number
  note?: string
}

export interface WorkOrderEvent {
  id: number
  woId: string
  fromStatus?: string
  toStatus: string
  actor: string
  atTime: string
  note?: string
}

export interface ParamVersionInfo {
  version: string
  createdAt: string
  observedCnt: number
  publicCnt: number
  assumedCnt: number
  totalCnt: number
}

export function getPickup(code: string, siteId = 'NH-TAOYUAN') {
  return call<PickupInfo>(`/api/pickup/${encodeURIComponent(code)}?siteId=${encodeURIComponent(siteId)}`)
}

export function getCarrierStats(siteId = 'NH-TAOYUAN') {
  return call<CarrierStat[]>(`/api/stats/carriers?siteId=${encodeURIComponent(siteId)}`)
}

export function getRuns(scenarioId?: string) {
  const q = scenarioId ? `?scenarioId=${encodeURIComponent(scenarioId)}` : ''
  return call<RunRow[]>(`/api/simulations${q}`)
}

export function getParamVersions() {
  return call<ParamVersionInfo[]>('/api/params/versions')
}

export function getWorkOrderEvents(id: string) {
  return call<WorkOrderEvent[]>(`/api/workorders/${encodeURIComponent(id)}/events`)
}
