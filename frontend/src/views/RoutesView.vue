<script setup lang="ts">
/**
 * P6 运输与轨迹：把"校门 → 四站"的配送路径画出来，并按到车批次推进车辆位置。
 * 路径来自 OSM 道路中心线 + Dijkstra（data/geo/station_routes.json），不是手绘示意线。
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Truck, MapPin, Clock } from 'lucide-vue-next'
import routesData from '@/data/station_routes.json'
import { SITES } from '@/data/sites'
import { useAppStore } from '@/stores/app'
import { useReveal } from '@/composables/useReveal'

interface Route {
  site_id: string
  name: string
  reachable: boolean
  length_m?: number
  minutes?: number
  polyline?: [number, number][]
}

const data = routesData as any
const routes = data.routes as Route[]
const gate = data.gate as { name: string; lon: number; lat: number }

/** 经纬度 → SVG 坐标（按所有折线的包围盒等比投影） */
const proj = computed(() => {
  const pts: [number, number][] = []
  routes.forEach((r) => r.polyline?.forEach((p) => pts.push(p)))
  pts.push([gate.lon, gate.lat])
  const lons = pts.map((p) => p[0])
  const lats = pts.map((p) => p[1])
  const minLon = Math.min(...lons), maxLon = Math.max(...lons)
  const minLat = Math.min(...lats), maxLat = Math.max(...lats)
  const pad = 0.15
  const w = 100, h = 100
  return {
    x: (lon: number) => ((lon - minLon) / (maxLon - minLon || 1)) * w * (1 - pad * 2) + w * pad,
    y: (lat: number) => h - (((lat - minLat) / (maxLat - minLat || 1)) * h * (1 - pad * 2) + h * pad)
  }
})

const paths = computed(() =>
  routes
    .filter((r) => r.reachable && r.polyline)
    .map((r) => ({
      ...r,
      d: r.polyline!.map((p, i) => `${i === 0 ? 'M' : 'L'}${proj.value.x(p[0]).toFixed(2)},${proj.value.y(p[1]).toFixed(2)}`).join(' ')
    }))
)

/** 演示时钟：07:00 起算，30 分钟一桶 */
const store = useAppStore()
const minute = ref(8 * 60 + 30)
const playing = ref(false)
let timer: number | undefined

const clock = computed(() => {
  const h = Math.floor(minute.value / 60)
  const m = minute.value % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
})

/** 三趟车：08:30 早班、12:30 补车、16:00 二次补车 */
const batches = computed(() => {
  const start = [8 * 60 + 30, 12 * 60 + 30, 16 * 60]
  return start.map((s, i) => ({ id: `B${i + 1}`, depart: s, leave: clockOf(s) }))
})
function clockOf(mins: number) {
  return `${String(Math.floor(mins / 60)).padStart(2, '0')}:${String(mins % 60).padStart(2, '0')}`
}

/** 每趟车当前走到哪：按最长路线的分钟数归一 */
const longest = computed(() => Math.max(...routes.filter((r) => r.reachable).map((r) => r.minutes ?? 1)))

const vehicles = computed(() =>
  batches.value.map((b) => {
    const elapsed = minute.value - b.depart
    const ratio = elapsed < 0 ? 0 : Math.min(1, elapsed / longest.value)
    return { ...b, ratio, pending: elapsed < 0, done: ratio >= 1 && elapsed > 0 }
  })
)

function pointAt(r: Route, ratio: number) {
  const pts = r.polyline
  if (!pts || !pts.length) return null
  const idx = Math.min(pts.length - 1, Math.floor(ratio * (pts.length - 1)))
  const p = pts[idx]
  return { x: proj.value.x(p[0]), y: proj.value.y(p[1]) }
}

const siteDots = computed(() =>
  SITES.map((s) => {
    const r = routes.find((x) => x.site_id === s.id)
    return { ...s, route: r, pos: r?.polyline?.length ? pointAt(r, 1) : null }
  })
)

function tick() {
  minute.value += 2
  if (minute.value > 19 * 60) {
    minute.value = 7 * 60
  }
}
onMounted(() => {
  timer = window.setInterval(() => {
    if (playing.value) tick()
  }, 120)
})
onUnmounted(() => window.clearInterval(timer))

useReveal('.panel')
</script>

<template>
  <div class="rt">
    <div class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><Truck :size="15" /> 校内配送路径与车次</h2>
        <span class="panel__hint">路网来自 OSM 道路中心线，Dijkstra 求解，非手绘示意</span>
      </div>
      <div class="panel__body rt__body">
        <svg class="rt__map" viewBox="0 0 100 100" role="img" aria-label="校内配送路径示意">
          <path v-for="p in paths" :key="p.site_id" :d="p.d" class="rt__line" />
          <g>
            <circle :cx="proj.x(gate.lon)" :cy="proj.y(gate.lat)" r="1.8" class="rt__gate" />
            <text :x="proj.x(gate.lon) + 2.4" :y="proj.y(gate.lat) + 0.8" class="rt__tag">北门</text>
          </g>
          <g v-for="s in siteDots" :key="s.id">
            <circle v-if="s.pos" :cx="s.pos.x" :cy="s.pos.y" r="1.5" :fill="s.color" />
            <text v-if="s.pos" :x="s.pos.x + 2" :y="s.pos.y + 0.6" class="rt__tag">{{ s.shortName }}</text>
          </g>
          <g v-for="(v, vi) in vehicles.filter((x) => !x.pending)" :key="v.id">
            <circle
              v-for="r in paths"
              :key="r.site_id + v.id"
              :cx="pointAt(r, v.ratio)?.x"
              :cy="pointAt(r, v.ratio)?.y"
              r="1.1"
              class="rt__veh"
              :style="{ opacity: 1 - vi * 0.25 }"
            />
          </g>
        </svg>

        <div class="rt__side">
          <div class="rt__clock">
            <span class="num">{{ clock }}</span>
            <button class="btn btn--primary" @click="playing = !playing">
              {{ playing ? '暂停' : '播放' }}
            </button>
            <button class="btn" @click="minute = 8 * 60 + 30; playing = false">复位</button>
          </div>
          <table class="rt__tbl">
            <thead><tr><th>站点</th><th>里程</th><th>用时</th></tr></thead>
            <tbody>
              <tr v-for="r in routes" :key="r.site_id">
                <td>{{ r.name }}</td>
                <td class="num">{{ r.reachable ? r.length_m + ' m' : '—' }}</td>
                <td class="num">{{ r.reachable ? r.minutes + ' min' : '不连通' }}</td>
              </tr>
            </tbody>
          </table>
          <p class="rt__note">
            兰苑在现有 OSM 路网中不连通，需补约 60 m 连接段；补绘后即可接入。
            车速按校内电动三轮 15 km/h 估算。
          </p>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><Clock :size="15" /> 到车批次</h2>
        <span class="panel__hint">按“早班进城 / 午间补车 / 二次补车”三个窗口</span>
      </div>
      <div class="panel__body">
        <ul class="rt__batches">
          <li v-for="b in vehicles" :key="b.id">
            <span class="tag tag--sim">{{ b.id }}</span>
            <b>{{ b.leave }} 发车</b>
            <span class="num">{{ Math.round(b.ratio * 100) }}%</span>
            <span v-if="b.pending" class="tag">未发车</span>
            <span v-else-if="b.done" class="tag tag--ok">已送达</span>
            <span v-else class="tag tag--sim">在途</span>
          </li>
        </ul>
        <p class="rt__note">
          <MapPin :size="12" /> 车辆位置按“出发时刻 + 路径用时”线性插值；一批快递跟着这辆车走完全程。
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rt { display: grid; gap: var(--sp-5); }
.rt__body { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: var(--sp-4); }
.rt__map { width: 100%; height: auto; background: var(--bg-2); border-radius: var(--r-md); }
.rt__line { fill: none; stroke: var(--brand); stroke-width: 0.5; opacity: 0.55; }
.rt__gate { fill: var(--ok); stroke: #fff; stroke-width: 0.3; }
.rt__veh { fill: #fff; stroke: var(--brand); stroke-width: 0.4; }
.rt__tag { font-size: 2.2px; fill: var(--fg-1); }
.rt__side { display: grid; gap: var(--sp-3); align-content: start; }
.rt__clock { display: flex; align-items: center; gap: var(--sp-2); }
.rt__clock .num { font-size: var(--fs-xl); font-weight: 600; }
.rt__tbl { width: 100%; font-size: var(--fs-xs); border-collapse: collapse; }
.rt__tbl th { text-align: left; color: var(--fg-2); font-weight: 600; padding: 4px 0; border-bottom: 1px solid var(--line); }
.rt__tbl td { padding: 4px 0; border-bottom: 1px dashed var(--line); }
.rt__note { font-size: var(--fs-xs); color: var(--fg-2); line-height: var(--lh-loose); }
.rt__batches { display: grid; gap: var(--sp-2); }
.rt__batches li { display: flex; align-items: center; gap: var(--sp-2); font-size: var(--fs-sm); }
@media (max-width: 1100px) {
  .rt__body { grid-template-columns: minmax(0, 1fr); }
}
</style>
