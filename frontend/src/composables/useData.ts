/**
 * 数据访问层。
 * 第 1 段：全部读内置样例数据（dataMode = 'local'）。
 * 第 3 段：把这里换成 fetch('/api/**')，失败时自动回落本地样例。
 *
 * 后端接口约定（第 2 段实现，字段与本文件中的类型完全一致）：
 *   GET /api/sites                       -> SiteStatic[]
 *   GET /api/sites/{id}                  -> SiteStatic
 *   GET /api/scenarios                   -> ScenarioBundle
 *   GET /api/stats/overview?scenario=id  -> { scenario, kpis, timeline }
 *   POST /api/simulation/run             -> { timeline, summary }   （请求体为 scenario）
 *   GET /api/incidents                   -> Incident[]
 *   PATCH /api/incidents/{id}            -> Incident
 *   POST /api/demo/reset                 -> { ok: true }
 */
import { computed, ref, shallowRef, unref, type Ref } from 'vue'
import type { Scenario, ScenarioBundle, SimRow, SiteStatic } from '@/data/types'
import bundle from '@/data/scenarios.json'
import { SITES } from '@/data/sites'

const localBundle = bundle as unknown as ScenarioBundle

/**
 * 当前生效的数据包。默认是内置样例；后端可用时由 initDataSource() 换成接口数据。
 * 用 shallowRef 是因为整包替换、不做深响应——深代理 13 万字节的数组只会白白变慢。
 */
const remote = shallowRef<ScenarioBundle | null>(null)
const data = computed(() => remote.value ?? localBundle)

/** 切换到后端数据；传 null 表示退回内置样例 */
export function setRemoteBundle(next: ScenarioBundle | null) {
  remote.value = next
}

export function useScenarioBundle() {
  return data.value
}

export function useScenarios() {
  return data.value.scenarios
}

/**
 * 取某个场景。id 支持字符串、ref 或 getter——必须支持后两者，
 * 否则页面拿到的是"切换前"的固定值，场景切换不会触发重算。
 */
export function useScenario(id: string | Ref<string> | (() => string)) {
  return computed<Scenario>(() => {
    const key = typeof id === 'function' ? id() : unref(id)
    const list = data.value.scenarios
    return list.find((s) => s.scenario_id === key) ?? list[0]
  })
}

/** 某场景下某站的时段仿真序列 */
export function simSeries(scenario: Scenario, siteId: string): SimRow[] {
  const idx = scenario.sites.findIndex((s) => s.site_id === siteId)
  if (idx < 0) return []
  return scenario.timeline.map((t) => t.sites[idx])
}

/** 全场景 KPI 汇总 */
export interface Kpi {
  totalArrivals: number
  totalPickups: number
  peakQ: number
  peakI: number
  riskBuckets: number
  riskSites: number
  unmet: number
}

export function scenarioKpi(scenario: Scenario): Kpi {
  const sum = scenario.summary
  return {
    totalArrivals: scenario.total_daily_arrivals,
    totalPickups: scenario.total_daily_pickups,
    peakQ: Math.max(...sum.map((s) => s.peak_q)),
    peakI: Math.max(...sum.map((s) => s.peak_i)),
    riskBuckets: sum.reduce((a, s) => a + s.risk_buckets, 0),
    riskSites: sum.filter((s) => s.risk_buckets > 0).length,
    unmet: sum.reduce((a, s) => a + s.unmet, 0)
  }
}

/** 站点在某场景下的汇总 */
export function siteSummary(scenario: Scenario, siteId: string) {
  return scenario.summary.find((s) => s.site_id === siteId)
}

export function useSites(): SiteStatic[] {
  return SITES
}

/** 演示时钟：默认取"真实当前时间"落在哪个时间桶，越界则夹到营业区间 */
export function currentBucketIndex(buckets: string[], now = new Date()): number {
  const m = now.getHours() * 60 + now.getMinutes()
  let best = 0
  let bestDiff = Infinity
  buckets.forEach((b, i) => {
    const [h, mm] = b.split(':').map(Number)
    const diff = Math.abs(h * 60 + mm - m)
    if (diff < bestDiff) { bestDiff = diff; best = i }
  })
  return best
}

/** 数据来源元信息，随真实数据源变化，所以做成 computed */
export const dataMeta = computed(() => ({
  warning: data.value.warning,
  generatedAt: data.value.generated_at,
  bucketMinutes: data.value.model.bucket_minutes,
  formulas: data.value.model.formulas,
  buckets: data.value.buckets
}))

/** 供后续切换到后端时复用的加载状态 */
export const loading = ref(false)
export const loadError = ref<string | null>(null)
