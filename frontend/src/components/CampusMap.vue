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
import { useAppStore } from '@/stores/app'
import type { Scenario } from '@/data/types'

const props = defineProps<{
  scenario: Scenario
  selectedId?: string | null
}>()

const emit = defineEmits<{ (e: 'select', id: string): void }>()

type LayerKind = 'satellite' | 'manual'
const layer = ref<LayerKind>('manual')

const el = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let satLayer: L.TileLayer | null = null
let manualLayer: L.ImageOverlay | null = null
const markers = new Map<string, L.Marker>()
const store = useAppStore()

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
    const p = store.sitePos(site.id)
    const m = L.marker([p.lat, p.lng], {
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
  if (layer.value === 'satellite') {
    if (manualLayer) { manualLayer.remove(); manualLayer = null }
    if (!satLayer) {
      satLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19, attribution: '影像 © Esri, Maxar, Earthstar Geographics' }
      )
    }
    satLayer.addTo(map)
  } else {
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
  map.attributionControl.setPrefix('')

  applyLayer()
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
watch(riskSiteIds, () => buildMarkers())
watch(() => store.siteOverride, () => buildMarkers(), { deep: true })
watch(manualBounds, (b) => manualLayer?.setBounds(b))

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
      const p = store.sitePos(site.id)
      map.flyTo([p.lat, p.lng], 17, { duration: 0.6 })
    }
  }
)

defineExpose({ setLayer: (l: LayerKind) => (layer.value = l) })

const layerOptions = [
  { id: 'manual' as const, label: '手册原图', hint: '学生手册原图 · 离线可用' },
  { id: 'satellite' as const, label: '卫星影像', hint: 'Esri 在线瓦片 · 需联网' }
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
      站点位置可在顶栏「校准站点位置」里手动对齐，非测绘成果
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
