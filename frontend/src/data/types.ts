/** 与 data/demo/scenarios.json 对齐的类型定义。后端 DTO 必须与此一致。 */

export interface DemandRow {
  bucket: string
  arrivals: number
  capacity: number
  pickups: number
}

export type LoadLevel = 'normal' | 'watch' | 'limit' | 'overflow'

export interface SiteParams {
  capacity_per_bucket: number
  kappa_q: number
  kappa_i: number
  q0: number
  i0: number
  /** 物理储位数（照片/参数推算） */
  physical_slots?: number
  physical_source?: 'observed' | 'assumed'
  kappa_i_warn?: number
  aisle_m?: number
  counters?: number
  /** 站点建成时的常量（不随场景变化），用于"这是固定设施还是临时措施"的说明 */
  capacity_norm: number
  kappa_q_norm: number
  kappa_i_norm: number
}

export interface ScenarioSite {
  site_id: string
  site_name: string
  service_hours: { open: string; close: string; bucket_count: number }
  params: SiteParams
  daily_totals: { arrivals: number; pickups: number; peak_bucket_arrivals: number }
  demand: DemandRow[]
}

export interface WeekDaySite {
  site_id: string
  start_i: number
  end_i: number
  occupancy_pct: number
  level: LoadLevel
  projected: boolean
}

export interface WeekDay {
  day: number
  sites: WeekDaySite[]
}

export interface SiteSummary {
  site_id: string
  daily_arrivals: number
  daily_pickups: number
  peak_q: number
  peak_i: number
  physical_slots?: number
  occupancy_pct?: number
  level?: LoadLevel
  aisle_ok_pct?: number
  queue_min?: number
  i0?: number
  net_per_day?: number
  risk_buckets: number
  risk_q_buckets: number
  risk_i_buckets: number
  total_pickup: number
  unmet: number
  first_risk_bucket: string | null
}

export interface SimRow {
  bucket: string
  q: number
  i: number
  s: number
  p: number
  unmet: number
  risk_q: boolean
  risk_i: boolean
}

export interface TimelineRow {
  bucket: string
  sites: SimRow[]
}

export interface Scenario {
  scenario_id: string
  name: string
  day_index?: number
  week?: WeekDay[]
  classification: 'SIMULATED'
  note: string
  total_daily_arrivals: number
  total_daily_pickups: number
  sites: ScenarioSite[]
  summary: SiteSummary[]
  timeline: TimelineRow[]
}

export interface ScenarioBundle {
  schema_version: string
  generated_at: string
  warning: string
  classification: string
  model: { bucket_minutes: number; formulas: Record<string, string> }
  buckets: string[]
  scenarios: Scenario[]
}

/** 站点静态资料，与 data/nanhu_sites.json 对齐（此处只取演示需要的字段）。 */
export interface SiteStatic {
  id: string
  name: string
  shortName: string
  role: 'main_hub' | 'unmanned'
  roleLabel: string
  area: string
  locationText: string
  hours: { open: string; close: string }
  services: string[]
  color: string
  /** 地图坐标：OSM 近似经纬度（演示近似，非测绘成果） */
  lat: number
  lng: number
  /** 手册原图像素坐标 */
  px: number
  py: number
}

