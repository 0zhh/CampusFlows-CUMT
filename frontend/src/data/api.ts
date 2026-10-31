/**
 * 后端访问层（第 3 段联调用）。现在后端还没写，调用一定会失败，
 * 但**失败必须无声降级**：页面继续用内置样例，只在顶栏亮出「演示数据模式」。
 * 这样答辩时后端没起来也能演，起来了就自动切真数据。
 */
import type { ScenarioBundle, SiteStatic } from './types'

/** 单次请求超时，超过就当后端不在 */
const TIMEOUT_MS = 2500

async function getJson<T>(url: string): Promise<T | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(url, { signal: ctrl.signal, headers: { Accept: 'application/json' } })
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    // 网络不通、超时、CORS、后端未启动，统统走本地样例
    return null
  } finally {
    clearTimeout(timer)
  }
}

export interface RemoteData {
  bundle: ScenarioBundle
  sites: SiteStatic[] | null
}

/**
 * 尝试取后端数据。只要场景包拿不到就整体返回 null，
 * 不做"一半真一半假"的拼接——混源的数据没法在页面上标清楚来源。
 */
export async function fetchRemote(): Promise<RemoteData | null> {
  const bundle = await getJson<ScenarioBundle>('/api/scenarios')
  if (!bundle || !Array.isArray(bundle.scenarios) || bundle.scenarios.length === 0) return null
  const sites = await getJson<SiteStatic[]>('/api/sites')
  return { bundle, sites }
}
