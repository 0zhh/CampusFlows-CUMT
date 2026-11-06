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
import { inboundAt, slotLabel, PEAK_DATE } from '@/composables/useFlows'
import { SITES } from '@/data/sites'

const SITE_LIST = SITES.map((s) => ({ id: s.id, name: s.shortName, color: s.color }))

function lineMeters(pts: [number, number][]) {
  let m = 0
  for (let i = 1; i < pts.length; i++) {
    const dy = (pts[i][1] - pts[i - 1][1]) * 110574
    const dx = (pts[i][0] - pts[i - 1][0]) * 111320 * Math.cos((34.21 * Math.PI) / 180)
    m += Math.hypot(dx, dy)
  }
  return m
}
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
/* ---------- 送货车：先选入口，再按 10 分钟批次跑 ---------- */
const gateId = ref<string>('north')
const slot = ref(78)                 // 13:00 前后，双十一当天午后
const playing = ref(true)
const progress = ref(0)              // 当前批次内车辆的行程比 0..1
const activeSite = ref<string | null>(null)

const SLOT_SECONDS = 6               // 演示：一个 10 分钟批次压缩成 6 秒
let tick: number | undefined

onMounted(() => {
  tick = window.setInterval(() => {
    if (!playing.value) return
    progress.value += 0.02
    if (progress.value >= 1) {
      progress.value = 0
      slot.value = (slot.value + 1) % 144
    }
  }, 120)
})
onUnmounted(() => window.clearInterval(tick))

const batchTime = computed(() => slotLabel(slot.value))
const nextTime = computed(() => slotLabel((slot.value + 1) % 144))

const gateRoutes = computed(() =>
  SITE_LIST.map((s) => {
    const pts = getLine(gateId.value, s.id)
    const meters = pts.length > 1 ? Math.round(lineMeters(pts)) : 0
    const parcels = inboundAt(PEAK_DATE, s.id, slot.value)
    return {
      ...s,
      meters,
      parcels,
      minutes: meters ? Math.round((meters / 1000) / 15 * 60) : 0,
      ready: pts.length > 1
    }
  })
)

const batchTotal = computed(() => gateRoutes.value.reduce((a, r) => a + r.parcels, 0))

function pickGate(id: string) {
  gateId.value = id
  activeSite.value = null
}
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
              <p>先选入口，地图上同时显示该入口出发的四条线路与在途车辆</p>
            </div>

            <div class="gate-seg" role="tablist" aria-label="选择校园入口">
              <button
                v-for="g in gates" :key="g.id"
                class="gate-seg__btn"
                :class="{ 'gate-seg__btn--on': gateId === g.id }"
                role="tab" :aria-selected="gateId === g.id"
                @click="pickGate(g.id)"
              >
                {{ g.name }}
              </button>
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
              :gate-id="gateId"
              :progress="progress"
              :active-site="activeSite"
              @select="emit('select', $event)"
              @mapclick="onMapClick"
              @truck="activeSite = activeSite === $event ? null : $event"
            />

            <aside class="mx__side">
              <div class="batch">
                <div class="batch__head">
                  <span class="batch__time num">{{ batchTime }}</span>
                  <button class="btn btn--ghost" @click="playing = !playing">
                    {{ playing ? '暂停' : '播放' }}
                  </button>
                </div>
                <p class="batch__sub">
                  第 {{ slot + 1 }} / 144 批 · 10 分钟一批 · 下一批 {{ nextTime }}
                </p>
                <p class="batch__sum">
                  本批共 <b class="num">{{ batchTotal }}</b> 件 · {{ gateRoutes.filter(r => r.parcels > 0).length }} 辆车在跑
                </p>
              </div>

              <h3 class="mx__sub"><Truck :size="14" /> {{ gates.find(g => g.id === gateId)?.name }}发出</h3>
              <ul class="mx__routes">
                <li
                  v-for="r in gateRoutes" :key="r.id"
                  :class="{ 'is-off': !r.ready, 'is-on': activeSite === r.id }"
                  @click="activeSite = activeSite === r.id ? null : r.id"
                >
                  <span class="mx__dot" :style="{ background: r.color }" />
                  <span class="mx__name">{{ r.name }}</span>
                  <span class="mx__num num">{{ r.ready ? r.meters + ' m · ' + r.minutes + ' min' : '未标注' }}</span>
                  <span class="mx__pkg num">{{ r.parcels }} 件</span>
                </li>
              </ul>

              <div v-if="activeSite" class="truck-card">
                <h4>{{ gateRoutes.find(r => r.id === activeSite)?.name }} · 在途</h4>
                <dl>
                  <div><dt>入口</dt><dd>{{ gates.find(g => g.id === gateId)?.name }}</dd></div>
                  <div><dt>批次</dt><dd>{{ batchTime }} 发出</dd></div>
                  <div><dt>本批到件</dt><dd>{{ gateRoutes.find(r => r.id === activeSite)?.parcels }} 件</dd></div>
                  <div><dt>里程</dt><dd>{{ gateRoutes.find(r => r.id === activeSite)?.meters }} m</dd></div>
                  <div><dt>预计送达</dt><dd>{{ gateRoutes.find(r => r.id === activeSite)?.minutes }} 分钟后</dd></div>
                </dl>
              </div>

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
                  八条线已经标好，这里只用来微调或重画某一条。选入口和站点后，点地图即可覆盖那一条。
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
                八条线来自你手绘的轨迹，已经过去重、抽稀和曲线平滑，只画在卫星底图上。
                哪条不对就点「描线」重画那一条。
              </p>
            </aside>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.gate-seg {
  display: inline-flex; padding: 3px; gap: 2px;
  background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-md);
}
.gate-seg__btn {
  padding: 6px 18px; border-radius: var(--r-sm); font-size: var(--fs-sm); color: var(--fg-1);
}
.gate-seg__btn--on { background: var(--brand); color: #fff; }
.batch { display: grid; gap: 4px; padding: var(--sp-2); background: var(--bg-2); border-radius: var(--r-md); }
.batch__head { display: flex; align-items: center; justify-content: space-between; }
.batch__time { font-size: var(--fs-lg); font-weight: 600; color: var(--fg-0); }
.batch__sub, .batch__sum { font-size: var(--fs-xs); color: var(--fg-2); }
.batch__sum b { color: var(--fg-0); }
.mx__routes li.is-on { background: var(--bg-3); color: var(--fg-0); }
.mx__pkg { color: var(--brand); font-size: 10px; }
.truck-card { padding: var(--sp-2); border: 1px solid var(--line); border-radius: var(--r-md); font-size: var(--fs-xs); }
.truck-card h4 { font-size: var(--fs-xs); color: var(--fg-1); margin-bottom: 4px; }
.truck-card dl { display: grid; gap: 2px; }
.truck-card div { display: flex; justify-content: space-between; }
.truck-card dt { color: var(--fg-2); }
.truck-card dd { color: var(--fg-0); }

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
.mx__routes li { display: grid; grid-template-columns: 8px minmax(0, 1fr) auto auto; gap: var(--sp-2); align-items: center; cursor: pointer; padding: 2px 4px; border-radius: var(--r-sm); }
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
