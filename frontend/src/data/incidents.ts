import type { Scenario, SimRow } from './types'

export type IncidentStatus = 'open' | 'doing' | 'closed'
export type IncidentLevel = 'high' | 'mid' | 'low'

export interface Incident {
  id: string
  siteId: string
  /** exceed = 已越阈值；watch = 接近阈值（预警）；drill = 流程演练样本 */
  kind: 'exceed' | 'watch' | 'drill'
  title: string
  level: IncidentLevel
  status: IncidentStatus
  bucket: string
  createdAt: string
  metric: string
  detail: string
  actions: { at: string; by: string; text: string }[]
}

const SITE_NAME: Record<string, string> = {
  'NH-TAOYUAN': '桃苑',
  'NH-SONGYUAN': '松苑',
  'NH-MEIYUAN': '梅苑',
  'NH-LANYUAN': '兰苑'
}

const short = (id: string) => SITE_NAME[id] ?? id

/** 预警线：占用达到阈值的这个比例就算"要盯住"，但还不算越限 */
const WATCH_LINE = 0.7

/** 把连续同类型的高风险时段压成一段，返回每段的首个下标与持续长度 */
function runsOf(rows: SimRow[], pred: (r: SimRow) => boolean) {
  const runs: { start: number; len: number }[] = []
  let cur: { start: number; len: number } | null = null
  rows.forEach((r, i) => {
    if (pred(r)) {
      if (cur) cur.len += 1
      else cur = { start: i, len: 1 }
    } else if (cur) {
      runs.push(cur)
      cur = null
    }
  })
  if (cur) runs.push(cur)
  return runs
}

/**
 * 由仿真结果自动生成风险工单。
 *
 * 两类工单：
 *   1. 越限工单 —— Q > κ_q 或 I > κ_i。按"同站 + 同类型 + 连续时段"合并，一段一张。
 *   2. 预警工单 —— 未越限但已达阈值 80%。每个站点最多一张，取占比最高的那个时段。
 * 越限工单只在本场景真的越限时出现，绝不虚构；无风险时靠预警工单撑起流程演示。
 */
export function generateIncidents(scenario: Scenario): Incident[] {
  const out: Incident[] = []
  let seq = 1

  scenario.sites.forEach((site, idx) => {
    const rows = scenario.timeline.map((t) => t.sites[idx])
    const p = site.params
    const name = short(site.site_id)

    const push = (inc: Omit<Incident, 'id' | 'createdAt' | 'actions'> & { actions: Incident['actions'] }) => {
      out.push({ ...inc, id: `WO-${String(seq++).padStart(3, '0')}`, createdAt: inc.bucket })
    }

    // ---- 1. 越限工单 ----
    const qRuns = runsOf(rows, (r) => r.risk_q)
    const iRuns = runsOf(rows, (r) => r.risk_i)

    for (const run of qRuns) {
      const r = rows[run.start]
      const peak = Math.max(...rows.slice(run.start, run.start + run.len).map((x) => x.q))
      push({
        siteId: site.site_id,
        kind: 'exceed',
        title: `${name} 积压超限`,
        level: 'high',
        status: 'open',
        bucket: r.bucket,
        metric: `未处理积压 ${r.q} 件 / 上限 ${p.kappa_q} 件（第 ${run.start + 1} 个时段，${r.bucket}）`,
        detail: `该时段到件量超过站点处理能力，未处理包裹开始累积，并持续 ${run.len} 个时段，峰值 ${peak} 件。持续超过 2 个时段会挤占分拣通道，需分流或增能。`,
        actions: [
          { at: r.bucket, by: '系统', text: `仿真监测到${name}积压 ${r.q} 件超过上限 ${p.kappa_q} 件，自动生成工单` },
          { at: r.bucket, by: '调度员', text: `向${name}增派 1 名分拣员，下一时段处理上限临时提高到 ${Math.round(p.capacity_per_bucket * 1.25)} 件` },
          { at: '待处理', by: '站点值守', text: '待确认：是否把部分到件改投就近无人站' }
        ]
      })
    }

    for (const run of iRuns) {
      const r = rows[run.start]
      const peak = Math.max(...rows.slice(run.start, run.start + run.len).map((x) => x.i))
      push({
        siteId: site.site_id,
        kind: 'exceed',
        title: `${name} 待取区超容`,
        level: 'mid',
        status: 'doing',
        bucket: r.bucket,
        metric: `待取库存 ${r.i} 件 / 上限 ${p.kappa_i} 件（第 ${run.start + 1} 个时段，${r.bucket}）`,
        detail: `已处理包裹在待取区积压，货架占用接近上限，并持续 ${run.len} 个时段，峰值 ${peak} 件。需引导取件或扩充暂存区，否则新到件无处上架。`,
        actions: [
          { at: r.bucket, by: '系统', text: `仿真监测到${name}待取库存 ${r.i} 件超过上限 ${p.kappa_i} 件，自动生成工单` },
          { at: r.bucket, by: '站点值守', text: '开放临时待取区，并在取件高峰前推送提醒短信' },
          { at: '进行中', by: '调度员', text: '跟进取件率，若两小时内未回落则申请跨站调拨' }
        ]
      })
    }

    // ---- 2. 预警工单：只在没有越限工单时补一张，避免刷屏 ----
    const hasExceed = out.some((x) => x.siteId === site.site_id && x.kind === 'exceed')
    if (!hasExceed) {
      let best = -1
      let bestRatio = 0
      rows.forEach((r, i) => {
        const ratio = Math.max(r.q / p.kappa_q, r.i / p.kappa_i)
        if (ratio >= WATCH_LINE && ratio > bestRatio) {
          bestRatio = ratio
          best = i
        }
      })
      if (best >= 0) {
        const r = rows[best]
        const qRatio = r.q / p.kappa_q
        const iRatio = r.i / p.kappa_i
        const byQ = qRatio >= iRatio
        push({
          siteId: site.site_id,
          kind: 'watch',
          title: `${name} ${byQ ? '积压' : '待取区'}接近上限`,
          level: 'low',
          status: 'closed',
          bucket: r.bucket,
          metric: byQ
            ? `未处理积压 ${r.q} 件 / 上限 ${p.kappa_q} 件，占用 ${Math.round(qRatio * 100)}%`
            : `待取库存 ${r.i} 件 / 上限 ${p.kappa_i} 件，占用 ${Math.round(iRatio * 100)}%`,
          detail: `未越限，但已超过阈值的 ${Math.round(WATCH_LINE * 100)}%，属于需要盯住的时段。本场景该站全程无越限，故按预警处理并已闭环。`,
          actions: [
            { at: r.bucket, by: '系统', text: `仿真监测到${name}占用达到 ${Math.round(Math.max(qRatio, iRatio) * 100)}%，生成预警` },
            { at: r.bucket, by: '站点值守', text: '加强现场引导，提前把大件移到临时暂存区' },
            { at: '已闭环', by: '系统', text: '后续时段占用回落，预警自动闭环' }
          ]
        })
      }
    }
  })

  // 兜底：整场确实一点压力都没有，也要能演示"派单 → 处理 → 闭环"的链路
  if (out.length === 0) {
    const site = scenario.sites[0]
    const p = site.params
    const rows = scenario.timeline.map((t) => t.sites[0])
    let peakIdx = 0
    rows.forEach((r, i) => { if (r.i > rows[peakIdx].i) peakIdx = i })
    const peak = rows[peakIdx]
    out.push({
      id: 'WO-001',
      siteId: site.site_id,
      kind: 'drill',
      title: `${short(site.site_id)} 流程演练`,
      level: 'low',
      status: 'closed',
      bucket: peak.bucket,
      createdAt: peak.bucket,
      metric: `待取库存 ${peak.i} 件 / 上限 ${p.kappa_i} 件（本场景峰值，未越限）`,
      detail: '本场景四站全程无越限，也没有接近阈值的时段。此工单为流程演示样本，用来说明「监测 → 派单 → 处理 → 闭环」的完整链路。',
      actions: [
        { at: peak.bucket, by: '系统', text: `仿真监测到${short(site.site_id)}进入当日取件高峰，自动建立观察工单` },
        { at: peak.bucket, by: '调度员', text: '确认现场人手充足，暂不调整处理能力' },
        { at: '已闭环', by: '站点值守', text: '取件高峰平稳度过，工单闭环' }
      ]
    })
  }

  return out
}
