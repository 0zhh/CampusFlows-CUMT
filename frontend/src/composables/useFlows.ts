/** 11 月 1—11 日的 10 分钟到件/取件数据（与运输批次同颗粒度） */
import { computed } from 'vue'
import raw from '@/data/nov_flows_10min.json'

interface Flow {
  dates: string[]
  times: string[]
  sites: string[]
  data: Record<string, Record<string, { in: number[]; out: number[] }>>
}

const flows = raw as unknown as Flow

export const DATES = flows.dates
export const TIMES = flows.times
export const SLOTS = flows.times.length

/** 演示默认用双十一当天 */
export const PEAK_DATE = '2026-11-11'

export function inboundAt(date: string, siteId: string, slot: number) {
  const d = flows.data[date]?.[siteId]
  if (!d || slot < 0 || slot >= d.in.length) return 0
  return d.in[slot]
}

export function outboundAt(date: string, siteId: string, slot: number) {
  const d = flows.data[date]?.[siteId]
  if (!d || slot < 0 || slot >= d.out.length) return 0
  return d.out[slot]
}

export function slotLabel(slot: number) {
  return flows.times[Math.min(Math.max(slot, 0), flows.times.length - 1)] ?? '00:00'
}

export const peakDate = computed(() => PEAK_DATE)
