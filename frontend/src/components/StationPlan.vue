<script setup lang="ts">
/**
 * 站点室内平面图（设计示意）
 * 数据来自 data/geo/station_layouts.json —— 由参数表生成，不是实测图纸。
 * 点某一排货架 → 展开该排的储位矩阵；点某个储位 → 显示该格的取件码与包裹信息。
 */
import { computed, ref } from 'vue'
import raw from '@/data/station_layouts.json'

interface Row {
  row_id: string
  zone_id: string
  col: number
  row_in_col: number
  x_m: number
  y_m: number
  length_m: number
  depth_m: number
  left_bays: number[]
  right_bays: number[]
  managed_by: 'SELF' | 'JD'
  tiers: number
  slots_per_tier: number
}
interface Zone { id: string; kind: string; label: string; x_m: number; y_m: number; w_m: number; h_m: number }
interface Station {
  station_id: string
  name: string
  floor: { width_m: number; depth_m: number; area_m2: number; area_note: string }
  params: Record<string, any>
  zones: Zone[]
  rows: Row[]
  status?: string
  note?: string
}

const props = defineProps<{ siteId: string }>()

const stations = (raw as any).stations as Station[]
const station = computed(() => stations.find((s) => s.station_id === props.siteId))

const selected = ref<Row | null>(null)
const selectedSlot = ref<{ bay: number; tier: number; idx: number } | null>(null)

/** 用一个稳定的哈希决定某格是否在架，保证每次打开看到的是同一批 */
function hash(str: string) {
  let h = 2166136261
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return (h >>> 0) / 4294967295
}

const CARRIERS = ['顺丰', '京东', '中通', '圆通', '韵达', '申通', 'EMS']

function slotState(bay: number, tier: number, idx: number) {
  const h = hash(`${bay}-${tier}-${idx}`)
  return h > 0.34
}
function slotCarrier(bay: number, tier: number, idx: number) {
  const h = hash(`c${bay}-${tier}-${idx}`)
  return CARRIERS[Math.floor(h * CARRIERS.length) % CARRIERS.length]
}
function slotCode(bay: number, tier: number, idx: number) {
  const seq = 1000 + Math.floor(hash(`s${bay}-${tier}-${idx}`) * 9000)
  return `${bay}-${tier}-${seq}`
}

const bayList = computed(() => {
  if (!selected.value) return [] as number[]
  return [...selected.value.left_bays, ...selected.value.right_bays]
})

const slots = computed(() => {
  if (!selected.value) return [] as { bay: number; tier: number; idx: number; on: boolean }[]
  const out: { bay: number; tier: number; idx: number; on: boolean }[] = []
  for (const bay of bayList.value) {
    for (let t = 1; t <= selected.value.tiers; t++) {
      for (let i = 0; i < selected.value.slots_per_tier; i++) {
        out.push({ bay, tier: t, idx: i, on: slotState(bay, t, i) })
      }
    }
  }
  return out
})

const occupancy = computed(() => {
  const arr = slots.value
  if (!arr.length) return 0
  return Math.round((arr.filter((s) => s.on).length / arr.length) * 100)
})

function pick(row: Row) {
  selected.value = selected.value?.row_id === row.row_id ? null : row
  selectedSlot.value = null
}
function pickSlot(bay: number, tier: number, idx: number) {
  selectedSlot.value = { bay, tier, idx }
}
</script>

<template>
  <div class="plan">
    <template v-if="station && !station.status">
      <div class="plan__head">
        <span class="plan__badge">设计示意</span>
        <span class="plan__meta">
          {{ station.floor.width_m }} × {{ station.floor.depth_m }} m ·
          约 {{ station.floor.area_m2 }} m² · {{ station.params.bays }} 架 × {{ station.params.tiers }} 层 ×
          {{ station.params.slots_per_tier }} 位
        </span>
      </div>

      <svg
        class="plan__svg"
        :viewBox="`-1 -1 ${station.floor.width_m + 2} ${station.floor.depth_m + 2}`"
        role="img"
        :aria-label="station.name + ' 室内平面示意图'"
      >
        <rect x="0" y="0" :width="station.floor.width_m" :height="station.floor.depth_m" class="floor" />

        <g v-for="z in station.zones" :key="z.id">
          <rect :x="z.x_m" :y="z.y_m" :width="z.w_m" :height="z.h_m" :class="'zone zone--' + z.kind" />
          <text :x="z.x_m + 0.4" :y="z.y_m + z.h_m / 2 + 0.35" class="zone__label">{{ z.label }}</text>
        </g>

        <g v-for="row in station.rows" :key="row.row_id" class="row" @click="pick(row)">
          <rect
            :x="row.x_m" :y="row.y_m" :width="row.length_m" :height="row.depth_m"
            :class="['rack', row.managed_by === 'JD' ? 'rack--jd' : 'rack--self',
                     selected && selected.row_id === row.row_id ? 'rack--on' : '']"
          />
          <text :x="row.x_m + 0.1" :y="row.y_m - 0.25" class="row__label">
            {{ row.left_bays[0] }}-{{ row.right_bays[row.right_bays.length - 1] }}
          </text>
        </g>
      </svg>

      <p class="plan__legend">
        <i class="sw sw--self" />自营货架　<i class="sw sw--jd" />京东管理 191—240　
        <i class="sw sw--scan" />扫码出库台　<i class="sw sw--sf" />顺丰收发区　<i class="sw sw--manual" />人工服务台
      </p>

      <div v-if="selected" class="shelf">
        <div class="shelf__head">
          <b>{{ selected.zone_id }} · 第 {{ selected.row_in_col + 1 }} 排</b>
          <span class="num">货架 {{ bayList[0] }}—{{ bayList[bayList.length - 1] }}</span>
          <span class="num">{{ selected.tiers }} 层 × {{ selected.slots_per_tier }} 位 = {{ bayList.length * selected.tiers * selected.slots_per_tier }} 个储位</span>
          <span class="shelf__occ num">在架 {{ occupancy }}%</span>
        </div>
        <div class="shelf__grid">
          <div v-for="t in selected.tiers" :key="t" class="shelf__tier">
            <span class="shelf__tierNo num">{{ t }} 层</span>
            <button
              v-for="s in slots.filter((x) => x.tier === t)"
              :key="`${s.bay}-${s.idx}`"
              class="slot"
              :class="{ 'slot--on': s.on, 'slot--sel': selectedSlot && selectedSlot.bay === s.bay && selectedSlot.tier === s.tier && selectedSlot.idx === s.idx }"
              :title="s.on ? `${s.bay}-${s.tier} 位 ${s.idx + 1}` : '空'"
              @click="s.on && pickSlot(s.bay, s.tier, s.idx)"
            />
          </div>
        </div>
        <p v-if="selectedSlot" class="shelf__detail">
          <b>取件码 {{ slotCode(selectedSlot.bay, selectedSlot.tier, selectedSlot.idx) }}</b>
          · {{ slotCarrier(selectedSlot.bay, selectedSlot.tier, selectedSlot.idx) }}
          · 位置：{{ selectedSlot.bay }} 号架 {{ selectedSlot.tier }} 层第 {{ selectedSlot.idx + 1 }} 位
          <span class="tag tag--sim">模拟</span>
        </p>
        <p v-else class="shelf__hint">点绿格查看该储位的取件码与承运商</p>
      </div>
    </template>

    <p v-else class="plan__empty">
      该站点还没有室内布局照片，暂不绘制示意平面图（避免凭空画）。桃苑主站可查看。
    </p>
  </div>
</template>

<style scoped>
.plan { display: grid; gap: var(--sp-2); }
.plan__head { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.plan__badge {
  font-size: 10px; padding: 1px 6px; border-radius: var(--r-pill);
  border: 1px dashed var(--line-strong); color: var(--warn-ink);
}
.plan__meta { font-size: var(--fs-xs); color: var(--fg-2); }

.plan__svg { width: 100%; height: auto; max-height: 300px; background: var(--bg-2); border-radius: var(--r-md); }
.floor { fill: var(--bg-1); }
.zone--entrance { fill: #3fa97c; }
.zone--counter { fill: #e8a33d; }
.zone--brand_sf { fill: #965c80; }
.zone--manual { fill: #5b9bd5; }
.zone__label { font-size: 0.55px; fill: #fff; }
.rack { stroke: var(--bg-0); stroke-width: 0.04; cursor: pointer; }
.rack--self { fill: #3d5170; }
.rack--jd { fill: #784ea0; }
.rack--on { stroke: var(--brand); stroke-width: 0.12; }
.row__label { font-size: 0.34px; fill: var(--fg-2); }

.plan__legend { font-size: 10px; color: var(--fg-2); display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.sw { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.sw--self { background: #3d5170; }
.sw--jd { background: #784ea0; }
.sw--scan { background: #e8a33d; }
.sw--sf { background: #965c80; }
.sw--manual { background: #5b9bd5; }

.shelf { border-top: 1px dashed var(--line); padding-top: var(--sp-2); display: grid; gap: var(--sp-2); }
.shelf__head { display: flex; gap: var(--sp-3); flex-wrap: wrap; font-size: var(--fs-xs); color: var(--fg-1); align-items: baseline; }
.shelf__occ { color: var(--brand); }
.shelf__grid { display: grid; gap: 3px; }
.shelf__tier { display: grid; grid-template-columns: 34px repeat(auto-fill, minmax(9px, 1fr)); gap: 2px; align-items: center; }
.shelf__tierNo { font-size: 10px; color: var(--fg-2); }
.slot { height: 9px; border-radius: 2px; background: var(--bg-3); border: 1px solid transparent; padding: 0; }
.slot--on { background: var(--ok); opacity: 0.75; }
.slot--sel { border-color: var(--brand); opacity: 1; }
.shelf__detail { font-size: var(--fs-xs); color: var(--fg-1); }
.shelf__hint { font-size: var(--fs-xs); color: var(--fg-2); }
.plan__empty { font-size: var(--fs-xs); color: var(--fg-2); }
</style>
