<script setup lang="ts">
/**
 * 南湖校区站点分布地图（Leaflet）
 * 两种底图：A 手册原图（默认，离线可用，四个红点就是站点真值）
 *           B 卫星影像（Esri 在线瓦片，需联网）
 * 坐标来自 store：校准过的用校准值，没校准的用 site_geolocation.json 的默认值。
 */
import { onMounted, onUnmounted, ref, watch, computed } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { SITES, isOpenNow } from '@/data/sites'
import { useAppStore, MANUAL_IMAGE } from '@/stores/app'
import type { Scenario } from '@/data/types'
import { gates as gateList, lines as routeLines } from '@/composables/useRoutes'

const props = defineProps<{
  scenario: Scenario
  selectedId?: string | null
  /** 是否叠加校内运输路径与车辆（放大视图里打开） */
  showRoutes?: boolean
  /** 描线模式：点地图取点 */
  trace?: boolean
  /** 描线模式的点（经纬度） */
  tracePoints?: { lat: number; lng: number }[]
  /** 只显示这个入口的线路；不传就全画 */
  gateId?: string | null
  /** 车辆在单条线路上的进度 0..1 */
  progress?: number
  /** 选中的车辆（站点 id） */
  activeSite?: string | null
}>()

const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'mapclick', p: { lat: number; lng: number }): void
  (e: 'truck', siteId: string): void
}>()

type LayerKind = 'satellite' | 'manual'
const layer = ref<LayerKind>('manual')
/** 卫星瓦片状态：没网时给个明确提示，而不是留一块灰 */
const satState = ref<'idle' | 'loading' | 'ok' | 'failed'>('idle')
let satErrors = 0

const el = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let satLayer: L.TileLayer | null = null
let manualLayer: L.ImageOverlay | null = null
const markers = new Map<string, L.Marker>()
let routeGroup: L.LayerGroup | null = null
let truckGroup: L.LayerGroup | null = null
const trucks = new Map<string, L.Marker>()
let vehicle: L.CircleMarker | null = null
let vehicleTimer: number | undefined
let traceLayer: L.Polyline | null = null
const store = useAppStore()

/** 离线卫星瓦片的覆盖范围（z14–z17 全区域，z18 核心区），与 data/research/fetch_sat_tiles.py 保持一致 */
const SAT_BOUNDS = L.latLngBounds([34.2000, 117.1180], [34.2320, 117.1620])

// 视野范围：OSM way 273639857 的外接矩形，取整后仅留极小外扩
const CAMPUS_BOUNDS = L.latLngBounds(
  [34.2065, 117.1295],
  [34.2232, 117.1506]
)

/** 手册原图的覆盖范围由 store 提供；校准后它会和四个站点坐标一起更新 */
const manualBounds = computed(() =>
  L.latLngBounds(
    [store.manualBounds.south, store.manualBounds.west],
    [store.manualBounds.north, store.manualBounds.east]
  )
)

const riskSiteIds = computed(() => {
  const set = new Set<string>()
  props.scenario?.summary?.forEach((s) => {
    if (s.risk_buckets > 0) set.add(s.site_id)
  })
  return set
})

/**
 * 站点位置：手工校准优先；否则手册底图用原图像素反算（红点在哪，标记就在哪），
 * 卫星底图用 WGS84 近似值。两张底图各有各的坐标真值，不能混用。
 */
function pixelToLatLng(site: (typeof SITES)[number]) {
  const b = store.manualBounds
  return {
    lat: b.north - (site.py / MANUAL_IMAGE.height) * (b.north - b.south),
    lng: b.west + (site.px / MANUAL_IMAGE.width) * (b.east - b.west)
  }
}

function posOf(site: (typeof SITES)[number]) {
  const o = store.siteOverride[site.id]
  if (o) return o
  return layer.value === 'manual' ? pixelToLatLng(site) : { lat: site.lat, lng: site.lng }
}

function siteIcon(site: (typeof SITES)[number]) {
  // 手册原图本来就把红点印在图上了，不再重复画彩色标记；
  // 但保留一个透明热区，点击照样能打开站点抽屉。
  if (layer.value === 'manual') {
    const risk = riskSiteIds.value.has(site.id)
    return L.divIcon({
      className: 'site-hit' + (risk ? ' site-hit--risk' : ''),
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      html: '<span class="site-hit__pad"></span>' + (risk ? '<span class="site-hit__ring"></span>' : '')
    })
  }

  const open = isOpenNow(site)
  const risk = riskSiteIds.value.has(site.id)
  const main = site.role === 'main_hub'
  const size = main ? 46 : 36
  const ring = risk ? '#e2605a' : open ? '#3ec9a7' : '#66727f'
  return L.divIcon({
    className: 'site-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    html: `
      <div class="sm ${risk ? 'sm--risk' : ''}" style="--c:${site.color};--ring:${ring};width:${size}px;height:${size}px">
        ${risk ? '<span class="sm__pulse"></span>' : ''}
        <span class="sm__dot"></span>
        <span class="sm__label">${site.shortName}</span>
      </div>
    `
  })
}

function buildMarkers() {
  if (!map) return
  markers.forEach((m) => m.remove())
  markers.clear()
  SITES.forEach((site) => {
    const p = posOf(site)
    const m = L.marker([p.lat, p.lng], {
      icon: siteIcon(site),
      zIndexOffset: site.role === 'main_hub' ? 500 : 0,
      keyboard: true,
      title: `${site.name}（${site.roleLabel}）`
    })
      .addTo(map!)
      .on('click', () => emit('select', site.id))

    // Leaflet 的标记能聚焦，但 Enter 不会触发 click；补上，键盘用户才能真正打开站点
    const node = m.getElement()
    node?.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        emit('select', site.id)
      }
    })
    m.bindTooltip(
      `<b>${site.name}</b><br/>${site.roleLabel} · ${site.locationText}<br/>${site.hours.open}—${site.hours.close}`,
      { direction: 'top', offset: [0, -14], className: 'site-tip' }
    )
    markers.set(site.id, m)
  })
}

function applyLayer() {
  if (!map) return
  if (layer.value === 'satellite') {
    if (manualLayer) { manualLayer.remove(); manualLayer = null }
    if (!satLayer) {
      satLayer = L.tileLayer('/tiles/sat/{z}/{x}/{y}.jpg', {
        minZoom: 14,
        maxZoom: 19,
        maxNativeZoom: 18,
        bounds: SAT_BOUNDS,
        attribution: '影像 © Esri, Maxar, Earthstar Geographics（本地缓存）'
      })
      satLayer.on('loading', () => {
        if (satState.value !== 'ok') satState.value = 'loading'
      })
      satLayer.on('load', () => {
        if (satState.value !== 'failed') satState.value = 'ok'
      })
      satLayer.on('tileerror', () => {
        satErrors += 1
        if (satErrors >= 3) satState.value = 'failed'
      })
    }
    satState.value = 'loading'
    satLayer.addTo(map)
  } else {
    satState.value = 'idle'
    satErrors = 0
    if (satLayer) { satLayer.remove(); satLayer = null }
    if (!manualLayer) {
      manualLayer = L.imageOverlay('/maps/cumtlive_logistics_locations.png', manualBounds.value, {
        opacity: 1,
        interactive: false
      })
    }
    manualLayer.addTo(map)
  }
}

function retrySat() {
  satErrors = 0
  satState.value = 'loading'
  satLayer?.redraw()
}

async function init() {
  if (!el.value) return

  map = L.map(el.value, {
    center: [34.2145, 117.1390],
    zoom: 16,
    minZoom: 14,
    maxZoom: 19,
    zoomSnap: 0,       // 允许小数级缩放，fitBounds 才能把原图铺满容器
    zoomDelta: 0.5,
    zoomControl: false,
    attributionControl: true
  })

  L.control.zoom({ position: 'bottomright' }).addTo(map)
  L.control.scale({ position: 'bottomleft', imperial: false }).addTo(map)
  map.attributionControl.setPrefix('')

  applyLayer()
  buildMarkers()
  map.on('click', (e: L.LeafletMouseEvent) => {
    if (props.trace) emit('mapclick', { lat: e.latlng.lat, lng: e.latlng.lng })
  })

  // 视野对准整个校区，四站落在校区西侧（与真实情况一致）
  map.fitBounds(CAMPUS_BOUNDS, { padding: [16, 16] })

  if (props.showRoutes && layer.value === 'satellite') drawRoutes()
  drawTrace()
  refit()
}

/** 描线预览：把已点的点连成虚线 */
let traceMarkers: L.CircleMarker[] = []
function drawTrace() {
  if (!map) return
  traceLayer?.remove()
  traceLayer = null
  traceMarkers.forEach((m) => m.remove())
  traceMarkers = []

  const pts = props.tracePoints ?? []
  pts.forEach((p, i) => {
    traceMarkers.push(
      L.circleMarker([p.lat, p.lng], {
        radius: i === pts.length - 1 ? 5 : 4,
        color: '#b26b00', weight: 2,
        fillColor: i === pts.length - 1 ? '#ffb037' : '#ffdba8',
        fillOpacity: 1
      }).addTo(map!)
    )
  })

  if (pts.length < 2) return
  traceLayer = L.polyline(pts.map((p) => [p.lat, p.lng] as [number, number]), {
    color: '#ffb037', weight: 4, opacity: 0.95, dashArray: '6 6'
  }).addTo(map)
}

function refit() {
  if (!map) return
  if (layer.value === 'manual') {
    map.fitBounds(manualBounds.value, { padding: [12, 12] })
    return
  }
  // 卫星层：有线路时框住线路本身，否则退回校区范围
  const pts = Object.values(routeLines.value).flat()
  if (props.showRoutes && pts.length > 1) {
    const b = L.latLngBounds(pts.map(([lon, lat]) => [lat, lon] as [number, number]))
    gateList.value.forEach((g) => b.extend([g.lat, g.lon]))
    map.fitBounds(b, { padding: [40, 40], maxZoom: 17 })
    return
  }
  map.fitBounds(CAMPUS_BOUNDS, { padding: [16, 16] })
}

let ro: ResizeObserver | null = null
let rafId = 0
onMounted(() => {
  void init().then(() => {
    if (!el.value) return
    // 容器尺寸一变就重算，永远按当前真实尺寸纠正 Leaflet 缓存的尺寸
    ro = new ResizeObserver(() => {
      if (!map) return
      cancelAnimationFrame(rafId)
      rafId = requestAnimationFrame(() => {
        map?.invalidateSize()
        refit()
      })
    })
    ro.observe(el.value)
    // 首帧之后再兜一次（面板刚插入时高度可能还没定型）
    window.setTimeout(() => {
      map?.invalidateSize()
      refit()
    }, 260)
  })
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  ro?.disconnect()
  clearRoutes()
  map?.remove()
  map = null
})

watch(layer, () => {
  applyLayer()
  refit()
  buildMarkers()
  if (props.showRoutes && layer.value === 'satellite') drawRoutes()
  else clearRoutes()
})
watch(riskSiteIds, () => buildMarkers())
watch(() => store.siteOverride, () => buildMarkers(), { deep: true })
watch(() => props.tracePoints, drawTrace, { deep: true })
watch(() => props.progress, updateTruckPositions)
watch(() => [props.gateId, props.activeSite] as const, () => {
  if (props.showRoutes && layer.value === 'satellite') drawRoutes()
})

watch(manualBounds, (b) => {
  manualLayer?.setBounds(b)
  buildMarkers()
})

watch(
  () => props.selectedId,
  (id) => {
    if (!map) return
    if (!id) {
      map.closePopup()
      return
    }
    const site = SITES.find((s) => s.id === id)
    if (site) {
      const p = posOf(site)
      map.flyTo([p.lat, p.lng], 17, { duration: 0.6 })
    }
  }
)

/* ---------- 校内运输路径（放大视图里显示） ---------- */
const SITE_COLOR: Record<string, string> = Object.fromEntries(SITES.map((s) => [s.id, s.color]))

/** 把经纬度折线转成 Leaflet 坐标，并返回累计长度，供车辆插值 */
function toPath(pts: [number, number][]) {
  const latlngs = pts.map(([lon, lat]) => L.latLng(lat, lon))
  const acc = [0]
  for (let i = 1; i < latlngs.length; i++) acc.push(acc[i - 1] + latlngs[i].distanceTo(latlngs[i - 1]))
  return { pts: latlngs, acc, total: acc[acc.length - 1] || 1 }
}

function pointAt(path: ReturnType<typeof toPath>, ratio: number) {
  const target = path.total * Math.min(1, Math.max(0, ratio))
  for (let i = 1; i < path.acc.length; i++) {
    if (path.acc[i] >= target) {
      const seg = path.acc[i] - path.acc[i - 1] || 1
      const t = (target - path.acc[i - 1]) / seg
      return L.latLng(
        path.pts[i - 1].lat + (path.pts[i].lat - path.pts[i - 1].lat) * t,
        path.pts[i - 1].lng + (path.pts[i].lng - path.pts[i - 1].lng) * t
      )
    }
  }
  return path.pts[path.pts.length - 1]
}

function drawRoutes() {
  if (!map) return
  clearRoutes()
  routeGroup = L.layerGroup().addTo(map)

  // 两个入口
  gateList.value.forEach((g) => {
    const icon = L.divIcon({
      className: 'gate-pin',
      iconSize: [18, 18],
      iconAnchor: [9, 9],
      html: '<span class="gate-pin__dot"></span>'
    })
    L.marker([g.lat, g.lon], { icon, keyboard: false })
      .addTo(routeGroup!)
      .bindTooltip(g.name + '（配送入口）', { direction: 'top', offset: [0, -10] })
  })

  const only = props.gateId ?? null
  const ready = Object.entries(routeLines.value).filter(
    ([key, pts]) => pts.length >= 2 && (!only || key.startsWith(only + ':'))
  )
  ready.forEach(([key, pts]) => {
    const [gateId, siteId] = key.split(':')
    const color = SITE_COLOR[siteId] ?? '#3f6fb5'
    const latlngs = pts.map(([lon, lat]) => [lat, lon] as [number, number])

    // 底衬：深色宽线，保证在任何底色上都能看清
    L.polyline(latlngs, { color: '#0b0f14', weight: 7, opacity: 0.22, interactive: false }).addTo(routeGroup!)

    L.polyline(latlngs, {
      color,
      weight: gateId === 'north' ? 4 : 3.5,
      opacity: 0.95,
      className: 'flow-line' + (gateId === 'east' ? ' flow-line--thin' : '')
    })
      .addTo(routeGroup!)
      .bindTooltip(
        (gateList.value.find((g) => g.id === gateId)?.name ?? gateId) +
          ' → ' + (SITES.find((s) => s.id === siteId)?.shortName ?? siteId),
        { sticky: true }
      )
  })

  drawTrucks()
}

/** 每个站点一辆车，沿线路跑 */
function drawTrucks() {
  if (!map) return
  trucks.forEach((m) => m.remove())
  trucks.clear()
  if (!truckGroup) truckGroup = L.layerGroup().addTo(map)
  else truckGroup.clearLayers()

  const only = props.gateId ?? null
  Object.entries(routeLines.value)
    .filter(([key, pts]) => pts.length >= 2 && (!only || key.startsWith(only + ':')))
    .forEach(([key, pts]) => {
      const [, siteId] = key.split(':')
      const active = props.activeSite === siteId
      const icon = L.divIcon({
        className: 'truck-pin' + (active ? ' truck-pin--on' : ''),
        iconSize: [34, 24],
        iconAnchor: [17, 12],
        html:
          '<span class="truck-pin__body">' +
          '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
          '<path d="M10 17h4V5H2v12h3"/><path d="M20 17h2v-3.34a4 4 0 0 0-1.17-2.83L19 9h-5v8h1"/>' +
          '<circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg></span>'
      })
      const marker = L.marker([pts[0][1], pts[0][0]], { icon, keyboard: false, zIndexOffset: 800 })
        .addTo(truckGroup!)
        .on('click', () => emit('truck', siteId))
      trucks.set(siteId, marker)
    })
  updateTruckPositions()
}

function updateTruckPositions() {
  const only = props.gateId ?? null
  const order = Object.keys(routeLines.value).sort()
  Object.entries(routeLines.value).forEach(([key, pts]) => {
    if (pts.length < 2 || (only && !key.startsWith(only + ':'))) return
    const [, siteId] = key.split(':')
    const marker = trucks.get(siteId)
    if (!marker) return
    const path = toPath(pts)
    // 按顺序错开一点，四辆车不会挤在门口
    const offset = (order.indexOf(key) % 4) * 0.07
    const p = pointAt(path, ((props.progress ?? 0) + offset) % 1)
    marker.setLatLng(p)
  })
}

function clearRoutes() {
  trucks.forEach((m) => m.remove())
  trucks.clear()
  truckGroup?.remove()
  truckGroup = null
  routeGroup?.remove()
  routeGroup = null
}

watch(
  () => [props.showRoutes, routeLines.value, gateList.value, layer.value] as const,
  () => {
    if (props.showRoutes && layer.value === 'satellite') drawRoutes()
    else clearRoutes()
  },
  { deep: true }
)

defineExpose({
  setLayer: (l: LayerKind) => (layer.value = l),
  /** 弹窗淡入后容器尺寸才定型，外部在动画结束后调一次 */
  refresh: () => {
    map?.invalidateSize()
    refit()
    if (props.showRoutes && layer.value === 'satellite') drawRoutes()
    else clearRoutes()
  }
})

const layerOptions = [
  { id: 'manual' as const, label: '手册原图', hint: '学生手册原图 · 离线可用' },
  { id: 'satellite' as const, label: '卫星影像', hint: '本地缓存 · 离线可用' }
]
</script>

<template>
  <div class="map-wrap">
    <div ref="el" class="map" role="application" aria-label="南湖校区站点分布地图" />

    <div class="map__layers" role="group" aria-label="底图切换">
      <button
        v-for="opt in layerOptions"
        :key="opt.id"
        class="layer-btn"
        :class="{ 'layer-btn--on': layer === opt.id }"
        :aria-pressed="layer === opt.id"
        @click="layer = opt.id"
      >
        <span class="layer-btn__label">{{ opt.label }}</span>
        <span class="layer-btn__hint">{{ opt.hint }}</span>
      </button>
    </div>

    <div v-if="layer === 'satellite'" class="map__legend">
      <span class="lg"><i class="lg__dot" style="background: var(--tao)" />桃苑主站</span>
      <span class="lg"><i class="lg__dot" style="background: var(--song)" />松苑</span>
      <span class="lg"><i class="lg__dot" style="background: var(--mei)" />梅苑</span>
      <span class="lg"><i class="lg__dot" style="background: var(--lan)" />兰苑</span>
      <span class="lg"><i class="lg__ring" />风险时段</span>
      <span v-if="showRoutes" class="lg"><i class="lg__line" />配送路径</span>
      <span v-if="showRoutes" class="lg"><i class="lg__gate" />配送入口</span>
    </div>
    <div v-if="layer === 'satellite' && satState === 'failed'" class="map__offline" role="status">
      <b>卫星瓦片加载失败</b>
      <span>本地离线瓦片没读到。可能是文件缺失或未构建，可重试或切回手册原图。</span>
      <div class="map__offline-actions">
        <button class="btn btn--primary" @click="layer = 'manual'">切回手册原图</button>
        <button class="btn" @click="retrySat">重试</button>
      </div>
    </div>

    <p v-else class="map__legend map__legend--plain">
      站点位置已在原图上用红点标出 · 点击可查看当前负荷
    </p>

    <p class="map__note">
      站点位置可在顶栏「校准站点位置」里手动对齐，非测绘成果
    </p>
  </div>
</template>

<style scoped>
/* 流动的配送线：虚线沿着路径跑 */
:deep(.flow-line) {
  stroke-dasharray: 22 16;
  stroke-linecap: round;
  animation: routeFlow 1.5s linear infinite;
}
:deep(.flow-line--thin) { stroke-dasharray: 16 18; animation-duration: 1.8s; }
@keyframes routeFlow {
  to { stroke-dashoffset: -38; }
}
@media (prefers-reduced-motion: reduce) {
  :deep(.flow-line) { animation: none; }
}

.gate-pin__dot {
  display: block; width: 14px; height: 14px; margin: 2px; border-radius: 50%;
  background: #2fa36b; border: 2px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,.5);
}
.lg__gate { width: 9px; height: 9px; border-radius: 50%; background: #2fa36b; display: inline-block; }
.truck-pin__body {
  display: grid; place-items: center;
  width: 26px; height: 26px; margin: 0 auto;
  background: #fff; border-radius: 50%;
  color: #2f6fb5;
  box-shadow: 0 2px 6px rgba(0, 0, 0, .45);
  border: 2px solid #2f6fb5;
  transform: translateY(-6px);
}
.truck-pin--on .truck-pin__body { border-color: #ffb037; box-shadow: 0 0 0 4px rgba(255, 176, 55, .35); }

.map__offline {
  position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
  z-index: 600; display: grid; gap: 6px; justify-items: center; text-align: center;
  padding: var(--sp-3) var(--sp-4); max-width: 320px;
  background: color-mix(in srgb, var(--bg-1) 94%, transparent);
  border: 1px solid var(--line-strong); border-radius: var(--r-md);
  backdrop-filter: blur(8px);
}
.map__offline b { font-size: var(--fs-sm); color: var(--fg-0); }
.map__offline span { font-size: var(--fs-xs); color: var(--fg-2); line-height: var(--lh-loose); }
.map__offline-actions { display: flex; gap: var(--sp-2); }

.site-hit__pad {
  display: block;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  transition: box-shadow 0.15s ease;
}
.site-hit__ring {
  position: absolute;
  inset: -7px;
  border-radius: 50%;
  border: 2px solid var(--danger);
  opacity: 0.85;
  animation: hitPulse 2.4s var(--ease) infinite;
  pointer-events: none;
}
.site-hit { position: relative; }
@keyframes hitPulse {
  0%, 100% { transform: scale(0.92); opacity: 0.5; }
  50% { transform: scale(1.08); opacity: 0.95; }
}
@media (prefers-reduced-motion: reduce) {
  .site-hit__ring { animation: none; }
}
.site-hit:hover .site-hit__pad {
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--brand) 55%, transparent);
  background: color-mix(in oklab, var(--brand) 14%, transparent);
}
.map__legend--plain { font-size: var(--fs-xs); color: var(--fg-2); }

.lg__line { width: 16px; height: 3px; border-radius: 2px; background: linear-gradient(90deg, var(--tao) 0 25%, var(--song) 25% 50%, var(--mei) 50% 75%, var(--lan) 75% 100%); display: inline-block; }

.map-wrap {
  position: relative;
  border-radius: var(--r-lg);
  overflow: hidden;
  border: 1px solid var(--line);
  background: var(--bg-1);
  isolation: isolate;
}

.map {
  height: 100%;
  min-height: 520px;
  width: 100%;
  background-color: #0a0f15;
  /* 底图未加载完（卫星瓦片要联网）时，用点阵表示"这里是空的"，
     而不是留一块纯黑让人以为地图挂了 */
  background-image: radial-gradient(circle, rgb(120 142 166 / 0.18) 1px, transparent 1px);
  background-size: 16px 16px;
}
[data-theme='light'] .map {
  background-color: #e3e8ee;
  background-image: radial-gradient(circle, rgb(120 138 158 / 0.22) 1px, transparent 1px);
}

.map__layers {
  position: absolute;
  top: var(--sp-3);
  right: var(--sp-3);
  z-index: 500;
  display: flex;
  gap: var(--sp-1);
  padding: var(--sp-1);
  border-radius: var(--r-md);
  background: color-mix(in srgb, var(--bg-1) 92%, transparent);
  backdrop-filter: blur(10px);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-2);
}

.layer-btn {
  display: grid;
  gap: 1px;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-sm);
  text-align: left;
  color: var(--fg-1);
  transition: background var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
}
.layer-btn:hover { background: var(--bg-2); color: var(--fg-0); }
.layer-btn--on { background: var(--bg-3); color: var(--fg-0); }
.layer-btn__label { font-size: var(--fs-sm); font-weight: 600; }
.layer-btn__hint { font-size: 10px; color: var(--fg-2); }

.map__legend {
  position: absolute;
  bottom: 46px;
  left: var(--sp-3);
  z-index: 500;
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-md);
  background: color-mix(in srgb, var(--bg-1) 92%, transparent);
  backdrop-filter: blur(10px);
  border: 1px solid var(--line);
  font-size: var(--fs-xs);
  color: var(--fg-1);
}
.lg { display: inline-flex; align-items: center; gap: var(--sp-1); }
.lg__dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.lg__ring {
  width: 9px; height: 9px; border-radius: 50%;
  border: 2px solid var(--danger); display: inline-block;
}

.map__note {
  position: absolute;
  right: var(--sp-3);
  bottom: var(--sp-3);
  z-index: 500;
  font-size: 10px;
  color: var(--fg-2);
  background: color-mix(in srgb, var(--bg-1) 85%, transparent);
  padding: 2px var(--sp-2);
  border-radius: var(--r-sm);
}
</style>

<style>
/* 站点标记（Leaflet 内部渲染，不能用 scoped） */
.site-marker { background: none; border: none; }

.sm {
  position: relative;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--c);
  border: 2px solid var(--ring);
  box-shadow: 0 0 0 3px rgb(0 0 0 / 0.45), 0 2px 12px rgb(0 0 0 / 0.5);
  cursor: pointer;
  transition: transform 160ms cubic-bezier(0.22, 0.61, 0.36, 1);
}
.sm:hover { transform: scale(1.12); }

.sm__dot {
  width: 34%;
  height: 34%;
  border-radius: 50%;
  background: rgb(255 255 255 / 0.92);
}

.sm__label {
  position: absolute;
  top: calc(100% + 3px);
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 3px rgb(0 0 0 / 0.9), 0 0 6px rgb(0 0 0 / 0.7);
  white-space: nowrap;
  pointer-events: none;
}

.sm--risk { animation: sm-shake 2.4s ease-in-out infinite; }
.sm__pulse {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px solid var(--ring);
  animation: sm-pulse 1.8s ease-out infinite;
  pointer-events: none;
}

@keyframes sm-pulse {
  0% { transform: scale(0.85); opacity: 0.9; }
  100% { transform: scale(1.5); opacity: 0; }
}
@keyframes sm-shake {
  0%, 100% { filter: none; }
  50% { filter: brightness(1.25); }
}

.site-tip {
  background: #10151c !important;
  border: 1px solid #35414f !important;
  color: #e9eef4 !important;
  font-size: 12px !important;
  line-height: 1.5 !important;
  padding: 6px 9px !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 24px rgb(0 0 0 / 0.5) !important;
}
.site-tip::before { border-top-color: #35414f !important; }

.feat-tip {
  background: #10151c !important;
  border: 1px solid #2a3543 !important;
  color: #9aa7b6 !important;
  font-size: 11px !important;
  padding: 2px 7px !important;
  border-radius: 5px !important;
  box-shadow: none !important;
}
.feat-tip::before { display: none !important; }

.leaflet-container { font-family: inherit; }
.leaflet-control-attribution {
  background: rgb(8 11 16 / 0.72) !important;
  color: #66727f !important;
  font-size: 10px !important;
}
.leaflet-control-attribution a { color: #9aa7b6 !important; }
.leaflet-control-zoom a {
  background: #171e27 !important;
  color: #9aa7b6 !important;
  border-color: #222c38 !important;
}
.leaflet-control-zoom a:hover { background: #202935 !important; color: #e9eef4 !important; }
.leaflet-control-scale-line {
  background: rgb(8 11 16 / 0.7) !important;
  border-color: #35414f !important;
  color: #9aa7b6 !important;
}
</style>
