import type { Ref } from 'vue'

/** 后端工单的最小形状（与 Spring Boot 的 WorkOrder 实体一致） */
export interface ApiWorkOrder {
  id: string
  siteId: string
  kind: string
  status: 'open' | 'doing' | 'closed'
  bucket: string
  title: string
  detail: string
}

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

/** 拉后端工单；后端不在就返回 null，调用方回落到本地生成 */
export function fetchWorkOrders(): Promise<ApiWorkOrder[] | null> {
  return call<ApiWorkOrder[]>('/api/workorders')
}

/** 把状态写回后端；失败不阻塞界面（本地状态照常生效） */
export function patchWorkOrder(id: string, status: string) {
  return call<ApiWorkOrder>(`/api/workorders/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  })
}

/** 一键复位 */
export function resetWorkOrders() {
  return call<ApiWorkOrder[]>('/api/workorders/reset', { method: 'POST' })
}

/** 把后端返回的状态映射成 id → status，用于覆盖本地工单 */
export function toStatusMap(list: ApiWorkOrder[] | null): Record<string, 'open' | 'doing' | 'closed'> {
  const map: Record<string, 'open' | 'doing' | 'closed'> = {}
  list?.forEach((w) => {
    map[w.id] = w.status
  })
  return map
}

export type StatusMap = Ref<Record<string, 'open' | 'doing' | 'closed'>>
