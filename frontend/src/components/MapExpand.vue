<script setup lang="ts">
/**
 * 校园地图放大视图：整屏地图 + 运输路径 + 驿站位置重置。
 * 运输轨迹页（P6）并到这里，不再单独占一个导航项。
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { X, RotateCcw, Truck, PencilLine, Copy, Eraser, Undo2, Download } from 'lucide-vue-next'
import CampusMap from './CampusMap.vue'
import { useAppStore, MANUAL_IMAGE } from '@/stores/app'
import { gates, getLine, setLine, summary, exportJson, resetAll } from '@/composables/useRoutes'
import type { Scenario } from '@/data/types'


const props = defineProps<{ open: boolean; scenario: Scenario; selectedId?: string | null }>()
const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'select', id: string): void
}>()

const store = useAppStore()
const mapRef = ref<InstanceType<typeof CampusMap> | null>(null)

watch(
  () => props.open,
  (on) => {
    if (!on) return
    // 等过渡结束、容器尺寸定型后再让 Leaflet 重算视野
    nextTick(() => window.setTimeout(() => (mapRef.value as any)?.refresh?.(), 280))
  }
)
const resetHint = ref(false)

/* ---------- 描线：选入口 + 选站点，点地图取点 ---------- */
const trace = ref(false)
const gateId = ref('north')
const target = ref('NH-TAOYUAN')
const copied = ref(false)

const currentLine = computed<[number, number][]>(() => getLine(gateId.value, target.value))
const points = computed(() => currentLine.value.map(([lng, lat]) => ({ lat, lng })))

const SITE_OPTIONS = [
  { id: 'NH-TAOYUAN', label: '桃苑主站' },
  { id: 'NH-SONGYUAN', label: '松苑' },
  { id: 'NH-MEIYUAN', label: '梅苑' },
  { id: 'NH-LANYUAN', label: '兰苑' }
]

const gateInfo = computed(() => gates.value.find((g) => g.id === gateId.value))

const traceJson = computed(() =>
  JSON.stringify({ gate_id: gateId.value, site_id: target.value, polyline: currentLine.value }, null, 0)
)

function onMapClick(p: { lat: number; lng: number }) {
  if (!trace.value) return
  const pts: [number, number][] = [
    ...currentLine.value,
    [Number(p.lng.toFixed(6)), Number(p.lat.toFixed(6))]
  ]
  setLine(gateId.value, target.value, pts)
}

function undo() {
  setLine(gateId.value, target.value, currentLine.value.slice(0, -1))
}

function clearTrace() {
  setLine(gateId.value, target.value, [])
}

async function copyTrace() {
  try {
    await navigator.clipboard.writeText(exportJson())
    copied.value = true
    window.setTimeout(() => (copied.value = false), 1800)
  } catch {
    copied.value = false
  }
}

function download() {
  const blob = new Blob([exportJson()], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'campus-routes.json'
  a.click()
  URL.revokeObjectURL(a.href)
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && trace.value) {
    e.stopPropagation()
    trace.value = false
  }
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))

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
              <p>两个入口 × 四个驿站，共 8 条线；描好后自动画线并跑车</p>
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
                <li v-for="s in summary" :key="s.gate.id + s.siteId" :class="{ 'is-off': s.count < 2 }">
                  <span class="mx__dot" :class="'mx__dot--' + s.siteId.slice(3, 6).toLowerCase()" />
                  <span class="mx__name">{{ s.gate.name }} → {{ s.siteName }}</span>
                  <span v-if="s.count >= 2" class="mx__num num">{{ s.count }} 点</span>
                  <span v-else class="mx__off">待标注</span>
                </li>
              </ul>
              <div v-if="trace" class="trace">
                <div class="trace__row">
                  <label class="trace__label" for="trace-gate">入口</label>
                  <select id="trace-gate" v-model="gateId" class="trace__select">
                    <option v-for="g in gates" :key="g.id" :value="g.id">{{ g.name }}</option>
                  </select>
                  <span v-if="gateInfo" class="trace__coord num">{{ gateInfo.lat.toFixed(5) }}, {{ gateInfo.lon.toFixed(5) }}</span>
                </div>

                <div class="trace__row">
                  <label class="trace__label" for="trace-target">去哪个站</label>
                  <select id="trace-target" v-model="target" class="trace__select">
                    <option v-for="o in SITE_OPTIONS" :key="o.id" :value="o.id">{{ o.label }}</option>
                  </select>
                </div>

                <p class="trace__hint">
                  从所选的入口开始，沿路一个点一个点点下去（可以拖地图再接着点）。每选一组入口+站点就是独立的一条线。
                </p>

                <p class="trace__count">
                  这条线已有 <b class="num">{{ points.length }}</b> 个点
                </p>

                <div class="trace__actions">
                  <button class="btn btn--ghost" :disabled="!points.length" @click="undo">
                    <Undo2 :size="13" /> 撤销
                  </button>
                  <button class="btn btn--ghost" :disabled="!points.length" @click="clearTrace">
                    <Eraser :size="13" /> 清空这条
                  </button>
                </div>


                <div class="trace__actions">
                  <button class="btn btn--primary" @click="copyTrace">
                    <Copy :size="13" /> {{ copied ? '已复制' : '复制全部' }}
                  </button>
                  <button class="btn" @click="download">
                    <Download :size="13" /> 下载
                  </button>
                  <button class="btn btn--ghost" @click="resetAll(); copied = false">
                    <Eraser :size="13" /> 全部清空
                  </button>
                </div>

                <p class="trace__tip">
                  描线时按 Esc 退出；点存在本机，刷新不丢。画完点「复制全部」发我，我写进项目数据。
                </p>
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
.trace__tip { font-size: 10px; color: var(--fg-2); line-height: 1.5; }
.trace__row { display: grid; grid-template-columns: 46px minmax(0, 1fr); align-items: center; gap: var(--sp-2); }
.trace__coord { grid-column: 2; font-size: 10px; color: var(--fg-2); }
.trace__sub { font-size: var(--fs-xs); color: var(--fg-2); margin-top: var(--sp-1); }
.trace__list { display: grid; gap: 2px; }
.trace__list li {
  display: flex; justify-content: space-between; gap: var(--sp-2);
  font-size: var(--fs-xs); color: var(--fg-2); cursor: pointer;
  padding: 2px 4px; border-radius: var(--r-sm);
}
.trace__list li:hover { background: var(--bg-2); }
.trace__list li.is-on { background: var(--bg-3); color: var(--fg-0); }
.trace__done { color: var(--ok); }
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
