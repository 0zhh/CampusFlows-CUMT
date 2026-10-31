<script setup lang="ts">
/**
 * 南湖校区矢量地图（Leaflet + 本地 OSM GeoJSON）
 * 三层底图：A 矢量校园（默认，离线可用）/ B 卫星影像 / C 手册原图对照
 */
import { onMounted, onUnmounted, ref, watch, computed } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { SITES, isOpenNow } from '@/data/sites'
import { useAppStore } from '@/stores/app'
import type { Scenario } from '@/data/types'

const props = defineProps<{
  scenario: Scenario
  selectedId?: string | null
}>()

const emit = defineEmits<{ (e: 'select', id: string): void }>()

type LayerKind = 'vector' | 'satellite' | 'manual'
const layer = ref<LayerKind>('vector')

const el = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let geoLayer: L.GeoJSON | null = null
let satLayer: L.TileLayer | null = null
let manualLayer: L.ImageOverlay | null = null
const markers = new Map<string, L.Marker>()
const store = useAppStore()

// 校区范围：OSM way 273639857「中国矿业大学(南湖校区)」的外接矩形
// bbox 34.20692..34.22281 / 117.13015..117.15010，取整后仅留极小外扩
const CAMPUS_BOUNDS = L.latLngBounds(
  [34.2065, 117.1295],
  [34.2232, 117.1506]
)

// 手册原图的"地理配准"：把 PNG 的四个角近似贴到校区范围上
// 这是演示用的近似对齐，不构成测绘配准
const MANUAL_BOUNDS = L.latLngBounds(
  [34.2040, 117.1250],
  [34.2250, 117.1530]
)

const riskSiteIds = computed(() => {
  const set = new Set<string>()
  props.scenario?.summary?.forEach((s) => {
    if (s.risk_buckets > 0) set.add(s.site_id)
  })
  return set
})

function styleFor(f: any): L.PathOptions {
  const kind: string = f.properties.kind ?? ''
  const dark = store.theme === 'dark'

  // 三级层次：画布 < 校园地面 < 建筑，保证暗色下也能一眼分清
  // 亮暗两套都用"画布 < 校园地面 < 建筑/水域 < 道路"的四级明度台阶，
  // 每级至少差 25 个亮度单位，缩到 700px 宽也能分清。
  const c = dark
    ? {
        bFill: '#3d5170', bLine: '#6b86a8',
        wFill: '#1a5c86', wLine: '#3b9fd4',
        gFill: '#24543a', gLine: '#3f8460',
        campusFill: '#222d3c', campusLine: '#46586e',
        trunk: '#899bb2', secondary: '#6d8098', minor: '#556678', path: '#445362'
      }
    : {
        bFill: '#b7c3d3', bLine: '#8c9bad',
        wFill: '#8cc3e8', wLine: '#5c9dcc',
        gFill: '#aed8b8', gLine: '#7bae88',
        campusFill: '#fbfcfe', campusLine: '#a3b1c2',
        trunk: '#a68a5c', secondary: '#bfab80', minor: '#d2c7ae', path: '#e2dac8'
      }

  if (kind === 'amenity=university') {
    return { color: c.campusLine, weight: 1, fillColor: c.campusFill, fillOpacity: 1 }
  }
  if (kind.startsWith('building')) {
    return { color: c.bLine, weight: 0.8, fillColor: c.bFill, fillOpacity: 0.95 }
  }
  if (kind.startsWith('natural=water') || kind.startsWith('leisure=swimming')) {
    return { color: c.wLine, weight: 1, fillColor: c.wFill, fillOpacity: 0.9 }
  }
  if (kind.startsWith('leisure')) {
    return { color: c.gLine, weight: 1, fillColor: c.gFill, fillOpacity: 0.85 }
  }
  if (kind.startsWith('highway')) {
    const hw = f.properties.highway
    if (['trunk', 'trunk_link', 'primary', 'primary_link'].includes(hw)) {
      return { color: c.trunk, weight: 2.6, opacity: 0.95 }
    }
    if (['secondary', 'secondary_link', 'tertiary', 'tertiary_link'].includes(hw)) {
      return { color: c.secondary, weight: 2, opacity: 0.95 }
    }
    if (['footway', 'path', 'steps', 'pedestrian', 'track', 'cycleway'].includes(hw)) {
      return { color: c.path, weight: 1.1, opacity: 0.9, dashArray: '3 3' }
    }
    return { color: c.minor, weight: 1.4, opacity: 0.95 }
  }
  return { color: c.campusLine, weight: 0.8, opacity: 0.6 }
}

function siteIcon(site: (typeof SITES)[number]) {
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
    const m = L.marker([site.lat, site.lng], {
      icon: siteIcon(site),
      zIndexOffset: site.role === 'main_hub' ? 500 : 0,
      keyboard: true,
      title: `${site.name}（${site.roleLabel}）`
    })
      .addTo(map!)
      .on('click', () => emit('select', site.id))
    m.bindTooltip(
      `<b>${site.name}</b><br/>${site.roleLabel} · ${site.locationText}<br/>${site.hours.open}—${site.hours.close}`,
      { direction: 'top', offset: [0, -14], className: 'site-tip' }
    )
    markers.set(site.id, m)
  })
}

function applyLayer() {
  if (!map) return
  if (geoLayer) geoLayer.setStyle(() => ({ opacity: 1 }))
  if (layer.value === 'vector') {
    if (satLayer) { satLayer.remove(); satLayer = null }
    if (manualLayer) { manualLayer.remove(); manualLayer = null }
    if (geoLayer && !map.hasLayer(geoLayer)) geoLayer.addTo(map)
  } else if (layer.value === 'satellite') {
    if (geoLayer) geoLayer.remove()
    if (manualLayer) { manualLayer.remove(); manualLayer = null }
    if (!satLayer) {
      satLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19, attribution: '影像 © Esri, Maxar, Earthstar Geographics' }
      )
    }
    satLayer.addTo(map)
  } else {
    if (geoLayer) geoLayer.remove()
    if (satLayer) { satLayer.remove(); satLayer = null }
    if (!manualLayer) {
      manualLayer = L.imageOverlay('/maps/cumtlive_logistics_locations.png', MANUAL_BOUNDS, {
        opacity: 1,
        interactive: false
      })
    }
    manualLayer.addTo(map)
  }
}

async function init() {
  if (!el.value) return

  map = L.map(el.value, {
    center: [34.2145, 117.1390],
    zoom: 16,
    minZoom: 14,
    maxZoom: 19,
    zoomControl: false,
    attributionControl: true
  })

  L.control.zoom({ position: 'bottomright' }).addTo(map)
  L.control.scale({ position: 'bottomleft', imperial: false }).addTo(map)

  map.attributionControl.setPrefix(
    '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap</a>'
  )

  const res = await fetch('/geo/cumt_nanhu_campus.geojson')
  const fc = await res.json()

  geoLayer = L.geoJSON(fc, {
    style: styleFor,
    onEachFeature: (f, lyr) => {
      const n = f.properties?.name
      if (n) lyr.bindTooltip(n, { sticky: true, className: 'feat-tip' })
    }
  })
  geoLayer.addTo(map)

  // 校区边界虚线（OSM way 273639857 的外接矩形，仅示意范围）
  L.rectangle(CAMPUS_BOUNDS, {
    color: '#e8a33d', weight: 1, dashArray: '6 6', fill: false, opacity: 0.22, interactive: false
  }).addTo(map)

  buildMarkers()

  // 视野对准整个校区，四站落在校区西侧（与真实情况一致）
  map.fitBounds(CAMPUS_BOUNDS, { padding: [16, 16] })
}

onMounted(init)

onUnmounted(() => {
  map?.remove()
  map = null
})

watch(layer, applyLayer)
watch(
  () => store.theme,
  () => {
    if (!geoLayer) return
    geoLayer.setStyle(styleFor as any)
  }
)
watch(riskSiteIds, () => buildMarkers())

watch(
  () => props.selectedId,
  (id) => {
    if (!map) return
    if (!id) {
      map.closePopup()
      return
    }
    const site = SITES.find((s) => s.id === id)
    if (site) map.flyTo([site.lat, site.lng], 17, { duration: 0.6 })
  }
)

defineExpose({ setLayer: (l: LayerKind) => (layer.value = l) })

const layerOptions = [
  { id: 'vector' as const, label: '矢量校园', hint: '本地 OSM · 离线可用' },
  { id: 'satellite' as const, label: '卫星影像', hint: 'Esri 在线瓦片 · 需联网' },
  { id: 'manual' as const, label: '手册原图', hint: '学生手册原图 · 近似配准' }
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

    <div class="map__legend">
      <span class="lg"><i class="lg__dot" style="background: var(--tao)" />桃苑主站</span>
      <span class="lg"><i class="lg__dot" style="background: var(--song)" />松苑</span>
      <span class="lg"><i class="lg__dot" style="background: var(--mei)" />梅苑</span>
      <span class="lg"><i class="lg__dot" style="background: var(--lan)" />兰苑</span>
      <span class="lg"><i class="lg__ring" />风险时段</span>
    </div>

    <p class="map__note">
      站点位置为按公开资料近似定位（约 ±150 m），非测绘成果
    </p>
  </div>
</template>

<style scoped>
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
  /* 校园多边形只覆盖约一半画幅，外面用极淡点阵填充，
     让人看出"这里是校区外、不在本图范围内"，而不是以为地图没加载完 */
  background-image: radial-gradient(circle, rgb(120 142 166 / 0.18) 1px, transparent 1px);
  background-size: 16px 16px;
}
[data-theme='light'] .map {
  background-color: #e3e8ee;
  background-image: radial-gradient(circle, rgb(120 138 158 / 0.22) 1px, transparent 1px);
}

/* 让 Leaflet 深色化 */
.map :deep(.leaflet-tile-pane) { filter: saturate(0.9); }

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
  left: var(--sp-3);
  bottom: var(--sp-3);
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
