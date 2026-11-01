<script setup lang="ts">
/**
 * 地图校准：把手册原图对齐到矢量底图，反解四站经纬度。
 *
 * 为什么需要它：手册原图是网页地图截图，投影和 OSM 不是同一套；
 * 而 OSM 在宿舍区几乎没有建筑物轮廓，没法用"建筑轮廓匹配"自动配准。
 * 所以做成"人眼对图 + 程序算坐标"：人只负责把图拖到位置，坐标由红点像素反算，
 * 不会出现"点着点着就偏了"。
 */
import { computed, onUnmounted, ref, watch, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { X, RotateCcw, Check, Copy, ZoomIn, ZoomOut, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Layers } from 'lucide-vue-next'
import { SITES } from '@/data/sites'
import { useAppStore, boundsAtScale, DEFAULT_M_PER_PX, CAMPUS_CENTER } from '@/stores/app'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', v: boolean): void }>()

const store = useAppStore()

const IMG_W = 1821
const IMG_H = 1123
/** 红点像素坐标（已按颜色连通域精确到 0.5 px） */
const DOTS: Record<string, [number, number]> = {
  'NH-TAOYUAN': [1396.5, 517.5],
  'NH-SONGYUAN': [839.6, 297.5],
  'NH-MEIYUAN': [377.5, 576.5],
  'NH-LANYUAN': [228.5, 977.5]
}

/** 打开面板时接着当前的覆盖范围（可能是上次校准的结果），没有就用默认比例尺 */
function initialBounds() {
  const b = store.manualBounds
  const usable = b && b.east > b.west && b.north > b.south
  return usable ? { ...b } : boundsAtScale(DEFAULT_M_PER_PX)
}

const bounds = ref(initialBounds())
const opacity = ref(0.62)
/** align = 拖动原图对齐；pick = 直接在地图上按顺序点四个站点 */
const mode = ref<'align' | 'pick'>('align')
const pickIndex = ref(0)
const picked = ref<Record<string, { lat: number; lng: number }>>({})
const copied = ref(false)
const el = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let overlay: L.ImageOverlay | null = null
let previews: L.LayerGroup | null = null
let geo: L.TileLayer | null = null

/** 站点坐标：点选模式用手点的，对齐模式由红点像素反算 */
const derived = computed(() =>
  SITES.map((s) => {
    const [px, py] = DOTS[s.id]
    const p = mode.value === 'pick' ? picked.value[s.id] : undefined
    return {
      id: s.id,
      shortName: s.shortName,
      color: s.color,
      picked: !!p,
      lat: p ? p.lat : bounds.value.north - (py / IMG_H) * (bounds.value.north - bounds.value.south),
      lng: p ? p.lng : bounds.value.west + (px / IMG_W) * (bounds.value.east - bounds.value.west)
    }
  })
)

const boundsLeaflet = computed(
  () => L.latLngBounds([bounds.value.south, bounds.value.west], [bounds.value.north, bounds.value.east])
)

function syncOverlay() {
  // 面板刚打开时地图还没建好，watcher 可能先触发，这里要挡一下
  if (!map || !previews) return
  overlay?.setBounds(boundsLeaflet.value)
  previews?.clearLayers()
  derived.value.forEach((d) => {
    L.circleMarker([d.lat, d.lng], {
      radius: d.picked ? 9 : 7,
      color: d.picked ? '#fff' : 'rgb(255 255 255 / 0.65)',
      weight: d.picked ? 3 : 2,
      fillColor: d.color,
      fillOpacity: 1
    })
      .bindTooltip(d.shortName, { direction: 'top', offset: [0, -8] })
      .addTo(previews!)
  })
}

function scaleAbout(f: number, anchor?: L.LatLng) {
  const b = bounds.value
  const cLng = anchor ? anchor.lng : (b.west + b.east) / 2
  const cLat = anchor ? anchor.lat : (b.south + b.north) / 2
  const fx = (cLng - b.west) / (b.east - b.west)
  const fy = (b.north - cLat) / (b.north - b.south)
  const w = (b.east - b.west) * f
  const h = (b.north - b.south) * f
  bounds.value = {
    west: cLng - fx * w,
    east: cLng - fx * w + w,
    north: cLat + fy * h,
    south: cLat + fy * h - h
  }
}

function nudge(dxPx: number, dyPx: number) {
  const b = bounds.value
  const perX = (b.east - b.west) / IMG_W
  const perY = (b.north - b.south) / IMG_H
  bounds.value = {
    west: b.west + dxPx * perX,
    east: b.east + dxPx * perX,
    north: b.north - dyPx * perY,
    south: b.south - dyPx * perY
  }
}

let dragFrom: { x: number; y: number; b: typeof bounds.value } | null = null

/** 切模式时清掉另一种模式留下的东西，免得两种结果混在一起 */
function switchMode(m: 'align' | 'pick') {
  mode.value = m
  picked.value = {}
  pickIndex.value = 0
  dragFrom = null
  // 对齐模式拖的是图片，点选模式拖的是地图
  if (map) m === 'pick' ? map.dragging.enable() : map.dragging.disable()
  syncOverlay()
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    e.stopPropagation()
    emit('update:open', false)
  }
}

function onMapClick(e: L.LeafletMouseEvent) {
  if (mode.value !== 'pick') return
  if (pickIndex.value >= SITES.length) return
  const site = SITES[pickIndex.value]
  if (!site) return
  picked.value = { ...picked.value, [site.id]: { lat: e.latlng.lat, lng: e.latlng.lng } }
  pickIndex.value = Math.min(SITES.length, pickIndex.value + 1)
  syncOverlay()
}

function onDown(e: PointerEvent) {
  if (!map || mode.value !== 'align') return
  dragFrom = { x: e.clientX, y: e.clientY, b: { ...bounds.value } }
  ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
}

function onMove(e: PointerEvent) {
  if (!dragFrom || !map) return
  const b0 = dragFrom.b
  const perX = (b0.east - b0.west) / IMG_W
  const perY = (b0.north - b0.south) / IMG_H
  const dx = (e.clientX - dragFrom.x) * perX
  const dy = (e.clientY - dragFrom.y) * perY
  bounds.value = { west: b0.west + dx, east: b0.east + dx, north: b0.north + dy, south: b0.south + dy }
}

function onUp() {
  dragFrom = null
}

function onWheel(e: WheelEvent) {
  if (!map) return
  e.preventDefault()
  const rect = (el.value as HTMLElement).getBoundingClientRect()
  const pt = map.containerPointToLatLng(L.point(e.clientX - rect.left, e.clientY - rect.top))
  const f = e.deltaY > 0 ? 1.04 : 0.96
  scaleAbout(Math.min(1.6, Math.max(0.62, f)), pt)
}

async function init() {
  await nextTick()
  if (!el.value || map) return
  map = L.map(el.value, {
    center: CAMPUS_CENTER,
    zoom: 16,
    zoomControl: false,
    dragging: false, // 拖拽留给图片，地图不跟着跑
    scrollWheelZoom: false,
    doubleClickZoom: false
  })

  // 对齐参照用卫星影像：它是真实地理位置的底，原图叠上去才好对
  geo = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 19, attribution: '影像 © Esri, Maxar, Earthstar Geographics' }
  ).addTo(map)

  overlay = L.imageOverlay('/maps/cumtlive_logistics_locations.png', boundsLeaflet.value, {
    opacity: opacity.value,
    interactive: false
  }).addTo(map)
  // 点选模式下把原图压淡一点，免得挡住卫星底图
  void 0

  map.on('click', onMapClick)
  previews = L.layerGroup().addTo(map)
  syncOverlay()
  map.fitBounds(L.latLngBounds([34.2065, 117.1295], [34.2232, 117.1506]), { padding: [10, 10] })
}

watch(
  () => props.open,
  async (v) => {
    if (v) {
      document.addEventListener('keydown', onKeydown)
      bounds.value = initialBounds()
      await init()
    } else {
      document.removeEventListener('keydown', onKeydown)
      map?.remove()
      map = null
      overlay = null
      previews = null
      geo = null
    }
  },
  { immediate: true }
)

watch(bounds, syncOverlay, { deep: true })
// 对齐模式要看清原图，点选模式要看清底图
watch(mode, (m) => {
  if (m === 'pick' && opacity.value > 0.35) opacity.value = 0.28
  if (m === 'align' && opacity.value < 0.35) opacity.value = 0.62
})
watch(opacity, (v) => overlay?.setOpacity(v))

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  map?.remove()
  map = null
})

function apply() {
  const o: Record<string, { lat: number; lng: number }> = {}
  derived.value.forEach((d) => {
    o[d.id] = { lat: Number(d.lat.toFixed(6)), lng: Number(d.lng.toFixed(6)) }
  })
  store.setSiteOverride(o)
  // 对齐模式下顺带把原图的覆盖范围存下来，切到「手册原图」底图时红点正好压在图标下面。
  // 点选模式没有对过原图，就别去动它，否则原图会被挪歪。
  if (mode.value === 'align') store.setManualBounds({ ...bounds.value })
  emit('update:open', false)
}

async function copyJson() {
  const o: Record<string, { lat: number; lng: number }> = {}
  derived.value.forEach((d) => {
    o[d.id] = { lat: Number(d.lat.toFixed(6)), lng: Number(d.lng.toFixed(6)) }
  })
  try {
    await navigator.clipboard.writeText(JSON.stringify(o, null, 2))
    copied.value = true
    setTimeout(() => (copied.value = false), 1800)
  } catch {
    copied.value = false
  }
}

function reset() {
  bounds.value = initialBounds()
  store.clearSiteOverride()
  store.clearManualBounds()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="cal">
      <div v-if="open" class="cal-root">
        <div class="cal-mask" @click="emit('update:open', false)" />
        <section class="cal" role="dialog" aria-modal="true" aria-label="地图校准">
          <header class="cal__head">
            <div>
              <h2>地图校准 · 把手册原图对齐到矢量底图</h2>
              <p>拖动图片、滚轮缩放，让原图的路和楼与底图重合。四个红点位置是固定的，对齐后坐标由程序反算。</p>
            </div>
            <button class="cal__close" aria-label="关闭" @click="emit('update:open', false)"><X :size="18" /></button>
          </header>

          <div class="cal__mode" role="tablist" aria-label="校准方式">
            <button
              class="cal__mode-btn"
              :class="{ 'cal__mode-btn--on': mode === 'align' }"
              role="tab"
              :aria-selected="mode === 'align'"
              @click="switchMode('align')"
            >
              ① 拖动原图对齐
              <em>原图叠在底图上，拖到路和楼重合</em>
            </button>
            <button
              class="cal__mode-btn"
              :class="{ 'cal__mode-btn--on': mode === 'pick' }"
              role="tab"
              :aria-selected="mode === 'pick'"
              @click="switchMode('pick')"
            >
              ② 直接点四个位置
              <em>按 桃苑 → 松苑 → 梅苑 → 兰苑 的顺序点地图</em>
            </button>
            <span v-if="mode === 'pick'" class="cal__progress">
              {{ pickIndex >= 4 ? '已点完，点「应用」生效' : '下一个：' + (SITES[pickIndex]?.shortName ?? '') }}
            </span>
          </div>

          <div class="cal__body">
            <div class="cal__map-wrap">
              <div
                ref="el"
                class="cal__map"
                @pointerdown="onDown"
                @pointermove="onMove"
                @pointerup="onUp"
                @pointercancel="onUp"
                @wheel="onWheel"
              />
              <div class="cal__tools">
                <button title="放大" @click="scaleAbout(0.96)"><ZoomIn :size="15" /></button>
                <button title="缩小" @click="scaleAbout(1.04)"><ZoomOut :size="15" /></button>
                <span class="cal__sep" />
                <button title="左移" @click="nudge(-6, 0)"><ArrowLeft :size="15" /></button>
                <button title="右移" @click="nudge(6, 0)"><ArrowRight :size="15" /></button>
                <button title="上移" @click="nudge(0, -6)"><ArrowUp :size="15" /></button>
                <button title="下移" @click="nudge(0, 6)"><ArrowDown :size="15" /></button>
              </div>
              <label class="cal__opacity">
                <Layers :size="13" />
                <input v-model.number="opacity" type="range" min="0" max="1" step="0.02" aria-label="原图不透明度" />
                <span class="num">{{ Math.round(opacity * 100) }}%</span>
              </label>
            </div>

            <aside class="cal__side">
              <h3>反算出的站点坐标</h3>
              <table class="cal__tbl">
                <thead><tr><th>站点</th><th>纬度</th><th>经度</th></tr></thead>
                <tbody>
                  <tr v-for="d in derived" :key="d.id">
                    <td><i class="dot" :style="{ background: d.color }" />{{ d.shortName }}</td>
                    <td class="num">{{ d.lat.toFixed(5) }}</td>
                    <td class="num">{{ d.lng.toFixed(5) }}</td>
                  </tr>
                </tbody>
              </table>
              <p class="cal__hint">
                对齐后点「应用」，四个站点图标会移到红点上，并记住在本机浏览器里。
                想写回源码就点「复制 JSON」发给我。
              </p>
              <div class="cal__acts">
                <button class="btn btn--primary" @click="apply"><Check :size="14" /> 应用</button>
                <button class="btn" @click="copyJson"><Copy :size="14" /> {{ copied ? '已复制' : '复制 JSON' }}</button>
                <button class="btn" @click="reset"><RotateCcw :size="14" /> 重置</button>
              </div>
            </aside>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.cal-root { position: fixed; inset: 0; z-index: 90; display: grid; place-items: center; }
.cal-mask { position: absolute; inset: 0; background: rgb(4 7 11 / 0.66); backdrop-filter: blur(3px); }
.cal {
  position: relative;
  width: min(1180px, 94vw);
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-1);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-2);
  overflow: hidden;
}
.cal__head {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--line);
}
.cal__head h2 { font-size: var(--fs-md); }
.cal__head p { font-size: var(--fs-xs); color: var(--fg-2); margin-top: 2px; }
.cal__head > div { flex: 1 1 auto; }
.cal__close {
  flex: 0 0 auto;
  display: grid; place-items: center;
  width: 30px; height: 30px; border-radius: var(--r-sm);
  color: var(--fg-1);
}
.cal__close:hover { background: var(--bg-2); color: var(--fg-0); }

.cal__mode {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-5);
  border-bottom: 1px solid var(--line);
  background: var(--bg-2);
}
.cal__mode-btn {
  display: grid;
  gap: 1px;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-sm);
  text-align: left;
  color: var(--fg-1);
  font-size: var(--fs-sm);
  border: 1px solid transparent;
}
.cal__mode-btn em { font-style: normal; font-size: 10px; color: var(--fg-2); }
.cal__mode-btn:hover { background: var(--bg-3); color: var(--fg-0); }
.cal__mode-btn--on {
  background: var(--brand-dim);
  color: var(--brand);
  border-color: rgb(232 163 61 / 0.35);
}
.cal__mode-btn--on em { color: rgb(232 163 61 / 0.75); }
.cal__progress { margin-left: auto; font-size: var(--fs-xs); color: var(--fg-1); }

.cal__body { display: grid; grid-template-columns: minmax(0, 1fr) 320px; min-height: 0; }
.cal__map-wrap { position: relative; border-right: 1px solid var(--line); }
.cal__map {
  height: 62vh;
  cursor: grab;
  touch-action: none;
  background: var(--bg-0);
}
.cal__map:active { cursor: grabbing; }

.cal__tools {
  position: absolute; left: var(--sp-3); top: var(--sp-3); z-index: 500;
  display: flex; align-items: center; gap: 2px;
  padding: 3px; border-radius: var(--r-md);
  background: color-mix(in srgb, var(--bg-1) 92%, transparent);
  border: 1px solid var(--line);
  backdrop-filter: blur(8px);
}
.cal__tools button {
  display: grid; place-items: center; width: 26px; height: 26px;
  border-radius: var(--r-sm); color: var(--fg-1);
}
.cal__tools button:hover { background: var(--bg-3); color: var(--fg-0); }
.cal__sep { width: 1px; height: 16px; background: var(--line); margin: 0 3px; }

.cal__opacity {
  position: absolute; left: var(--sp-3); bottom: var(--sp-3); z-index: 500;
  display: flex; align-items: center; gap: var(--sp-2);
  padding: 4px var(--sp-3); border-radius: var(--r-md);
  background: color-mix(in srgb, var(--bg-1) 92%, transparent);
  border: 1px solid var(--line);
  font-size: var(--fs-xs); color: var(--fg-1);
  backdrop-filter: blur(8px);
}
.cal__opacity input { width: 110px; }

.cal__side { padding: var(--sp-4) var(--sp-5); overflow-y: auto; }
.cal__side h3 { font-size: var(--fs-sm); margin-bottom: var(--sp-3); }
.cal__tbl { width: 100%; font-size: var(--fs-xs); border-collapse: collapse; }
.cal__tbl th {
  text-align: left; font-weight: 600; color: var(--fg-2);
  padding: 4px 6px; border-bottom: 1px solid var(--line);
}
.cal__tbl td { padding: 5px 6px; border-bottom: 1px dashed var(--line); }
.cal__tbl .dot {
  display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  margin-right: 6px; vertical-align: middle;
}
.cal__hint { margin-top: var(--sp-4); font-size: var(--fs-xs); color: var(--fg-2); line-height: var(--lh-loose); }
.cal__acts { margin-top: var(--sp-4); display: flex; flex-wrap: wrap; gap: var(--sp-2); }

.cal-enter-active, .cal-leave-active { transition: opacity 0.18s ease; }
.cal-enter-from, .cal-leave-to { opacity: 0; }
</style>
