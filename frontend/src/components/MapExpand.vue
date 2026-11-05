<script setup lang="ts">
/**
 * 校园地图放大视图：整屏地图 + 运输路径 + 驿站位置重置。
 * 运输轨迹页（P6）并到这里，不再单独占一个导航项。
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { X, RotateCcw, Truck, PencilLine, Copy, Eraser, Undo2, Download } from 'lucide-vue-next'
import CampusMap from './CampusMap.vue'
import { useAppStore, MANUAL_IMAGE } from '@/stores/app'
import type { Scenario } from '@/data/types'
import routesData from '@/data/station_routes.json'

const props = defineProps<{ open: boolean; scenario: Scenario; selectedId?: string | null }>()
const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'select', id: string): void
}>()

const store = useAppStore()
const mapRef = ref<InstanceType<typeof CampusMap> | null>(null)

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && trace.value) {
    e.stopPropagation()
    trace.value = false
  }
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))

watch(
  () => props.open,
  (on) => {
    if (!on) return
    // 等过渡结束、容器尺寸定型后再让 Leaflet 重算视野
    nextTick(() => window.setTimeout(() => (mapRef.value as any)?.refresh?.(), 280))
  }
)
const routes = (routesData as any).routes as {
  site_id: string
  name: string
  reachable: boolean
  pending?: boolean
  length_m?: number | null
  minutes?: number | null
  polyline?: [number, number][]
}[]
const resetHint = ref(false)

/* ---------- 描线：点地图取点，导出坐标 ---------- */
const TRACE_KEY = 'campusflow-trace-v1'
const trace = ref(false)
const target = ref('NH-TAOYUAN')
const copied = ref(false)

type Pt = { lat: number; lng: number }
function loadTrace(): Pt[] {
  try {
    const raw = localStorage.getItem(TRACE_KEY)
    const o = raw ? JSON.parse(raw) : null
    return Array.isArray(o?.points) ? o.points : []
  } catch {
    return []
  }
}
const points = ref<Pt[]>(loadTrace())
if (localStorage.getItem(TRACE_KEY)) {
  try {
    const o = JSON.parse(localStorage.getItem(TRACE_KEY) as string)
    if (o?.target) target.value = o.target
  } catch {
    /* 忽略 */
  }
}

watch(
  points,
  (list) => {
    try {
      localStorage.setItem(TRACE_KEY, JSON.stringify({ target: target.value, points: list }))
    } catch {
      /* 忽略 */
    }
  },
  { deep: true }
)
watch(target, () => {
  try {
    localStorage.setItem(TRACE_KEY, JSON.stringify({ target: target.value, points: points.value }))
  } catch {
    /* 忽略 */
  }
})

const SITE_OPTIONS = [
  { id: 'NH-TAOYUAN', label: '北门 → 桃苑主站' },
  { id: 'NH-SONGYUAN', label: '北门 → 松苑' },
  { id: 'NH-MEIYUAN', label: '北门 → 梅苑' },
  { id: 'NH-LANYUAN', label: '北门 → 兰苑' }
]

/** 折线同时给经纬度与原图像素坐标：像素是底图的稳定坐标系，反算不会漂 */
const pixels = computed(() => {
  const b = store.manualBounds
  return points.value.map((p) => [
    Math.round(((p.lng - b.west) / (b.east - b.west)) * MANUAL_IMAGE.width),
    Math.round(((b.north - p.lat) / (b.north - b.south)) * MANUAL_IMAGE.height)
  ])
})

const traceJson = computed(() =>
  JSON.stringify({
    site_id: target.value,
    points: points.value.map((p) => [Number(p.lng.toFixed(6)), Number(p.lat.toFixed(6))]),
    pixels: pixels.value
  })
)

function undo() {
  points.value = points.value.slice(0, -1)
}

function download() {
  const blob = new Blob([JSON.stringify({ site_id: target.value, points: points.value.map((p) => [Number(p.lng.toFixed(6)), Number(p.lat.toFixed(6))]), pixels: pixels.value }, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'route-' + target.value + '.json'
  a.click()
  URL.revokeObjectURL(a.href)
}

function onMapClick(p: { lat: number; lng: number }) {
  if (!trace.value) return
  points.value = [...points.value, p]
}

async function copyTrace() {
  try {
    await navigator.clipboard.writeText(traceJson.value)
    copied.value = true
    window.setTimeout(() => (copied.value = false), 1800)
  } catch {
    copied.value = false
  }
}

function clearTrace() {
  points.value = []
}

function resetPositions() {
  store.clearSiteOverride()
  resetHint.value = true
  window.setTimeout(() => (resetHint.value = false), 2200)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="mx">
      <div v-if="open" class="mx-root">
        <div class="mx-mask" @click="emit('update:open', false)" />
        <div class="mx" role="dialog" aria-modal="true" aria-label="校园地图放大视图">
          <header class="mx__head">
            <div class="mx__title">
              <h2>南湖校区 · 配送地图</h2>
              <p>配送起点为北门；线路待标注，描好后会自动画出并跑车</p>
            </div>
            <div class="mx__actions">
              <button class="btn btn--ghost" @click="resetPositions" title="把四个驿站恢复成默认坐标">
                <RotateCcw :size="14" /> 重置驿站位置
              </button>
              <button class="btn" :class="{ 'btn--primary': trace }" @click="trace = !trace"
                title="在地图上点出配送线路，导出坐标给我">
                <PencilLine :size="14" /> {{ trace ? '描线中' : '描线' }}
              </button>
              <span v-if="resetHint" class="mx__toast">已恢复默认位置</span>
              <button class="mx__close" aria-label="关闭" @click="emit('update:open', false)">
                <X :size="18" />
              </button>
            </div>
          </header>

          <div class="mx__body">
            <CampusMap
              ref="mapRef"
              :scenario="scenario"
              :selected-id="selectedId"
              show-routes
              :trace="trace"
              :trace-points="points"
              @select="emit('select', $event)"
              @mapclick="onMapClick"
            />

            <aside class="mx__side">
              <h3 class="mx__sub"><Truck :size="14" /> 线路一览</h3>
              <ul class="mx__routes">
                <li v-for="r in routes" :key="r.site_id" :class="{ 'is-off': !r.polyline?.length }">
                  <span class="mx__dot" :class="'mx__dot--' + r.site_id.slice(3, 6).toLowerCase()" />
                  <span class="mx__name">{{ r.name }}</span>
                  <span v-if="(r.polyline?.length ?? 0) >= 2" class="mx__num num">{{ r.length_m }} m · {{ r.minutes }} min</span>
                  <span v-else class="mx__off">待标注</span>
                </li>
              </ul>
              <div v-if="trace" class="trace">
                <label class="trace__label" for="trace-target">这条线去哪个站</label>
                <select id="trace-target" v-model="target" class="trace__select">
                  <option v-for="o in SITE_OPTIONS" :key="o.id" :value="o.id">{{ o.label }}</option>
                </select>

                <p class="trace__hint">
                  从校门开始，沿路一个点一个点点下去（可以拖动地图再接着点）。点完复制或下载发我。
                </p>

                <p class="trace__count">
                  已选 <b class="num">{{ points.length }}</b> 个点
                  <span v-if="points.length" class="trace__last">
                    · 最后一点 <span class="num">{{ pixels[points.length - 1][0] }}, {{ pixels[points.length - 1][1] }}</span> px
                  </span>
                </p>

                <div class="trace__actions">
                  <button class="btn btn--primary" :disabled="points.length < 2" @click="copyTrace">
                    <Copy :size="13" /> {{ copied ? '已复制' : '复制' }}
                  </button>
                  <button class="btn" :disabled="points.length < 2" @click="download">
                    <Download :size="13" /> 下载
                  </button>
                  <button class="btn btn--ghost" :disabled="!points.length" @click="undo">
                    <Undo2 :size="13" /> 撤销
                  </button>
                  <button class="btn btn--ghost" :disabled="!points.length" @click="clearTrace">
                    <Eraser :size="13" /> 清空
                  </button>
                </div>

                <pre v-if="points.length" class="trace__json">{{ traceJson }}</pre>
                <p class="trace__tip">描线时按 Esc 退出；点会存在本机，刷新不丢。</p>
              </div>

              <p class="mx__note">
                原来那四条按 OSM 道路算出来的线路已清空（与实际走法不符）。
                点「描线」在地图上手绘，复制或下载后发我即可落成正式路线。
              </p>
            </aside>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.trace { display: grid; gap: var(--sp-2); padding: var(--sp-2); border: 1px dashed var(--line-strong); border-radius: var(--r-md); }
.trace__label { font-size: var(--fs-xs); color: var(--fg-2); }
.trace__select { padding: 5px var(--sp-2); background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-sm); color: var(--fg-0); font-size: var(--fs-xs); }
.trace__last { color: var(--fg-2); }
.trace__tip { font-size: 10px; color: var(--fg-2); }
.trace__hint { font-size: var(--fs-xs); color: var(--fg-2); line-height: var(--lh-loose); }
.trace__count { font-size: var(--fs-xs); color: var(--fg-1); }
.trace__actions { display: flex; gap: var(--sp-2); }
.trace__json { font-size: 10px; color: var(--fg-2); background: var(--bg-2); padding: 6px; border-radius: var(--r-sm); max-height: 96px; overflow: auto; word-break: break-all; }

.mx-root { position: fixed; inset: 0; z-index: 260; display: grid; place-items: center; }
.mx-mask { position: absolute; inset: 0; background: rgba(8, 12, 18, 0.62); backdrop-filter: blur(3px); }
.mx {
  position: relative;
  width: min(1560px, 96vw);
  height: min(900px, 92vh);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
  overflow: hidden;
}
.mx__head {
  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--line);
}
.mx__title h2 { font-size: var(--fs-lg); font-weight: 600; color: var(--fg-0); }
.mx__title p { font-size: var(--fs-xs); color: var(--fg-2); }
.mx__actions { display: flex; align-items: center; gap: var(--sp-2); }
.mx__toast { font-size: var(--fs-xs); color: var(--ok-ink, var(--ok)); }
.mx__close {
  width: 30px; height: 30px; display: grid; place-items: center;
  border-radius: var(--r-sm); border: 1px solid var(--line); color: var(--fg-1);
}
.mx__body { display: grid; grid-template-columns: minmax(0, 1fr) 300px; min-height: 0; }
.mx__side {
  border-left: 1px solid var(--line);
  padding: var(--sp-3);
  display: grid; gap: var(--sp-2); align-content: start;
  overflow: auto;
}
.mx__sub { display: flex; align-items: center; gap: 6px; font-size: var(--fs-sm); font-weight: 600; color: var(--fg-0); }
.mx__routes { display: grid; gap: 6px; font-size: var(--fs-xs); }
.mx__routes li { display: grid; grid-template-columns: 8px minmax(0, 1fr) auto; gap: var(--sp-2); align-items: center; }
.mx__routes li.is-off { opacity: 0.55; }
.mx__dot { width: 8px; height: 8px; border-radius: 50%; background: var(--fg-2); }
.mx__dot--tao { background: var(--tao); }
.mx__dot--son { background: var(--song); }
.mx__dot--mei { background: var(--mei); }
.mx__dot--lan { background: var(--lan); }
.mx__name { color: var(--fg-1); }
.mx__num { color: var(--fg-2); font-variant-numeric: tabular-nums; }
.mx__off { color: var(--warn-ink); }
.mx__note { font-size: var(--fs-xs); color: var(--fg-2); line-height: var(--lh-loose); }

.mx-enter-active, .mx-leave-active { transition: opacity 0.2s ease; }
.mx-enter-from, .mx-leave-to { opacity: 0; }

@media (max-width: 1100px) {
  .mx__body { grid-template-columns: minmax(0, 1fr); }
  .mx__side { border-left: none; border-top: 1px solid var(--line); }
}
</style>
