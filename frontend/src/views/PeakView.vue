<script setup lang="ts">
import { computed, ref } from 'vue'
import { TrendingUp, TriangleAlert, ArrowLeftRight } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import { useScenarios, useScenario, simSeries } from '@/composables/useData'
import { SITES } from '@/data/sites'
import { useChartTheme } from '@/composables/useChartTheme'
import EChart from '@/components/EChart.vue'
import ScenarioPicker from '@/components/ScenarioPicker.vue'
import { onMounted } from 'vue'
import { getRuns, type RunRow } from '@/data/mysql'
import { useReveal } from '@/composables/useReveal'

const store = useAppStore()
const { t, tooltip, axisCommon } = useChartTheme()

const scenarios = useScenarios()
const scenario = useScenario(() => store.scenarioId)

/** 对比对象：高峰场景固定与常态对比；其余场景与高峰对比 */
const baseId = computed(() => (store.scenarioId === 'S2-PEAK' ? 'S1-NORMAL' : 'S2-PEAK'))
const baseScenario = useScenario(baseId)

const focusSite = ref('NH-TAOYUAN')

/** 把仿真结果与该站的需求行合并，图表里 A/C/D 和 Q/I 一起用 */
function merged(sc: typeof scenario.value, siteId: string) {
  const series = simSeries(sc, siteId)
  const demand = sc.sites.find((s) => s.site_id === siteId)?.demand ?? []
  return series.map((r, i) => ({
    ...r,
    arrivals: demand[i]?.arrivals ?? 0,
    capacity: demand[i]?.capacity ?? 0,
    pickups: demand[i]?.pickups ?? 0
  }))
}

const rows = computed(() => merged(scenario.value, focusSite.value))
const baseRows = computed(() => merged(baseScenario.value, focusSite.value))
const siteParams = computed(() => scenario.value.sites.find((s) => s.site_id === focusSite.value)!.params)
const baseParams = computed(() => baseScenario.value.sites.find((s) => s.site_id === focusSite.value)!.params)

const buckets = computed(() => scenario.value.timeline.map((x) => x.bucket))

/** 双库存堆叠图：未处理 Q + 待取 I */
const stockOption = computed(() => ({
  grid: { left: 48, right: 18, top: 36, bottom: 30 },
  tooltip: { trigger: 'axis', ...tooltip.value, axisPointer: { type: 'shadow' } },
  legend: { top: 0, right: 0, icon: 'roundRect', itemWidth: 9, itemHeight: 9, textStyle: { color: t.value.text, fontSize: 11 } },
  xAxis: {
    type: 'category', data: buckets.value, ...axisCommon.value, splitLine: { show: false },
    axisLabel: { color: t.value.text, fontSize: 10, interval: 3 }
  },
  yAxis: { type: 'value', ...axisCommon.value, name: '件', nameTextStyle: { color: t.value.text, fontSize: 10 } },
  series: [
    {
      name: '未处理积压 Q', type: 'bar', stack: 'stock', data: rows.value.map((r) => r.q),
      itemStyle: { color: '#e2605a' }, barWidth: '62%'
    },
    {
      name: '待取库存 I', type: 'bar', stack: 'stock', data: rows.value.map((r) => r.i),
      itemStyle: { color: '#3ec9a7', borderRadius: [3, 3, 0, 0] }
    },
    {
      name: '积压上限 κ_q', type: 'line', data: rows.value.map(() => siteParams.value.kappa_q),
      symbol: 'none', lineStyle: { width: 1.2, type: 'dashed', color: '#e8a33d' }
    }
  ]
}))

/** 需求 vs 能力 */
const demandOption = computed(() => ({
  grid: { left: 48, right: 18, top: 36, bottom: 30 },
  tooltip: { trigger: 'axis', ...tooltip.value, axisPointer: { type: 'shadow' } },
  legend: { top: 0, right: 0, icon: 'roundRect', itemWidth: 9, itemHeight: 9, textStyle: { color: t.value.text, fontSize: 11 } },
  xAxis: {
    type: 'category', data: buckets.value, ...axisCommon.value, splitLine: { show: false },
    axisLabel: { color: t.value.text, fontSize: 10, interval: 3 }
  },
  yAxis: { type: 'value', ...axisCommon.value, name: '件', nameTextStyle: { color: t.value.text, fontSize: 10 } },
  series: [
    {
      name: '到件量 A', type: 'bar', data: rows.value.map((r) => r.arrivals),
      itemStyle: { color: 'rgba(232,163,61,0.75)', borderRadius: [3, 3, 0, 0] }, barWidth: '55%'
    },
    {
      name: '处理上限 C', type: 'line', step: 'middle',
      data: rows.value.map((r) => r.capacity), symbol: 'none',
      lineStyle: { width: 2, color: '#5b9bd5' }
    },
    {
      name: '取件需求 D', type: 'line', data: rows.value.map((r) => r.pickups),
      symbol: 'none', smooth: 0.3, lineStyle: { width: 1.5, color: '#c05c8e', type: 'dashed' }
    }
  ]
}))

/** 基准 vs 调整 对比 */
const compareOption = computed(() => {
  const ids = SITES.map((s) => s.id)
  const names = SITES.map((s) => s.shortName)
  const pick = (sc: typeof scenario.value) => ids.map((id) => sc.summary.find((x) => x.site_id === id)!.peak_q)
  return {
    grid: { left: 48, right: 18, top: 36, bottom: 26 },
    tooltip: { trigger: 'axis', ...tooltip.value, axisPointer: { type: 'shadow' } },
    legend: { top: 0, right: 0, icon: 'roundRect', itemWidth: 9, itemHeight: 9, textStyle: { color: t.value.text, fontSize: 11 } },
    xAxis: { type: 'category', data: names, ...axisCommon.value, splitLine: { show: false } },
    yAxis: { type: 'value', ...axisCommon.value, name: '峰值积压（件）', nameTextStyle: { color: t.value.text, fontSize: 10 } },
    series: [
      { name: baseScenario.value.name, type: 'bar', data: pick(baseScenario.value), barWidth: '30%', itemStyle: { color: 'rgba(154,167,182,0.55)', borderRadius: [3, 3, 0, 0] } },
      { name: scenario.value.name, type: 'bar', data: pick(scenario.value), barWidth: '30%', itemStyle: { color: '#e8a33d', borderRadius: [3, 3, 0, 0] } }
    ]
  }
})

const runs = ref<RunRow[]>([])
const runId = ref<number | null>(null)
const pickedRun = computed(() => runs.value.find((r) => r.id === runId.value) ?? null)
const currentPeak = computed(() => Math.max(...rows.value.map((r) => r.i), 0))

onMounted(async () => {
  const list = await getRuns()
  if (list && list.length) {
    runs.value = list
    runId.value = list[0].id
  }
})

const riskRows = computed(() =>
  rows.value
    .map((r, i) => ({ ...r, idx: i }))
    .filter((r) => r.risk_q || r.risk_i)
)

const delta = computed(() => {
  const a = scenario.value.summary.reduce((x, s) => x + s.risk_buckets, 0)
  const b = baseScenario.value.summary.reduce((x, s) => x + s.risk_buckets, 0)
  return { now: a, base: b, diff: a - b }
})

useReveal(".kpis > *, .grid2 > *, .panel")
</script>

<template>
  <div class="pk">
    <div class="pk__bar">
      <ScenarioPicker />
      <div v-if="runs.length" class="runs">
        <label class="runs__label" for="run-select">历史运行</label>
        <select id="run-select" v-model.number="runId" class="runs__select">
          <option v-for="r in runs" :key="r.id" :value="r.id">
            第 {{ r.id }} 次 · {{ r.scenarioId }} · 峰值 {{ r.peakI }} 件
          </option>
        </select>
        <span v-if="pickedRun" class="runs__diff">
          与当前场景峰值 {{ currentPeak }} 件相比
          <b :class="pickedRun.peakI >= currentPeak ? 'up' : 'down'">
            {{ pickedRun.peakI >= currentPeak ? '+' : '' }}{{ pickedRun.peakI - currentPeak }}
          </b>
        </span>
      </div>
      <div class="pk__site" role="group" aria-label="选择站点">
        <button
          v-for="s in SITES"
          :key="s.id"
          class="chip"
          :class="{ 'chip--on': focusSite === s.id }"
          :aria-pressed="focusSite === s.id"
          @click="focusSite = s.id"
        >
          <i :style="{ background: s.color }" />{{ s.shortName }}
        </button>
      </div>
    </div>

    <section class="pk__summary">
      <div class="panel sum">
        <span class="sum__k"><TriangleAlert :size="14" /> 风险时段</span>
        <span class="sum__v num">{{ delta.now }}</span>
        <span class="sum__d" :class="delta.diff > 0 ? 'up' : delta.diff < 0 ? 'down' : ''">
          对比「{{ baseScenario.name }}」{{ delta.diff > 0 ? '+' : '' }}{{ delta.diff }}
        </span>
      </div>
      <div class="panel sum">
        <span class="sum__k"><TrendingUp :size="14" /> {{ SITES.find((s) => s.id === focusSite)?.shortName }} 峰值积压</span>
        <span class="sum__v num">{{ Math.max(...rows.map((r) => r.q)) }}</span>
        <span class="sum__d">上限 κ_q = {{ siteParams.kappa_q }} 件</span>
      </div>
      <div class="panel sum">
        <span class="sum__k"><ArrowLeftRight :size="14" /> 处理能力 C</span>
        <span class="sum__v num">{{ siteParams.capacity_per_bucket }}</span>
        <span class="sum__d">
          站点常量 {{ siteParams.capacity_norm }} 件/时段
          <template v-if="siteParams.capacity_per_bucket !== siteParams.capacity_norm">
            · 本场景加开临时处理位 ×{{ (siteParams.capacity_per_bucket / siteParams.capacity_norm).toFixed(2) }}
          </template>
          <template v-else> · 本场景未加开临时处理位</template>
        </span>
      </div>
      <div class="panel sum">
        <span class="sum__k">首个风险时段</span>
        <span class="sum__v">{{ riskRows[0]?.bucket ?? '无' }}</span>
        <span class="sum__d">{{ riskRows.length }} 个时段越过阈值</span>
      </div>
    </section>

    <section class="grid2">
      <div class="panel">
        <div class="panel__head">
          <h2 class="panel__title">双库存堆叠</h2>
          <span class="panel__hint">未处理积压 + 已处理待取 · 30 分钟一桶</span>
        </div>
        <div class="panel__body">
          <EChart :option="stockOption" :height="300" :empty="!rows.length" />
        </div>
      </div>

      <div class="panel">
        <div class="panel__head">
          <h2 class="panel__title">需求与处理能力</h2>
          <span class="panel__hint">C 是阶梯线，A 超过 C 即开始积压</span>
        </div>
        <div class="panel__body">
          <EChart :option="demandOption" :height="300" :empty="!rows.length" />
        </div>
      </div>
    </section>

    <section class="grid2">
      <div class="panel">
        <div class="panel__head">
          <h2 class="panel__title">方案对比：各站峰值积压</h2>
          <span class="panel__hint">{{ baseScenario.name }} vs {{ scenario.name }}</span>
        </div>
        <div class="panel__body">
          <EChart :option="compareOption" :height="280" />
        </div>
      </div>

      <div class="panel">
        <div class="panel__head">
          <h2 class="panel__title">风险时段清单</h2>
          <span class="panel__hint">{{ SITES.find((s) => s.id === focusSite)?.shortName }} · 共 {{ riskRows.length }} 个</span>
        </div>
        <div class="panel__body">
          <div v-if="riskRows.length" class="risk-list">
            <div class="risk-head">
              <span>时段</span><span>到件</span><span>处理</span><span>积压 Q</span><span>待取 I</span><span>触因</span>
            </div>
            <div class="risk-scroll">
              <div v-for="r in riskRows" :key="r.bucket" class="risk-row">
                <span class="num">{{ r.bucket }}</span>
                <span class="num">{{ r.arrivals }}</span>
                <span class="num">{{ r.capacity }}</span>
                <span class="num" :class="{ hot: r.risk_q }">{{ r.q }}</span>
                <span class="num" :class="{ hot: r.risk_i }">{{ r.i }}</span>
                <span>
                  <span v-if="r.risk_q" class="tag tag--danger">积压超限</span>
                  <span v-if="r.risk_i" class="tag tag--danger">待取超容</span>
                </span>
              </div>
            </div>
          </div>
          <p v-else class="empty">本场景该站点全程未越过阈值，无需干预。</p>
        </div>
      </div>
    </section>

    <div class="panel model">
      <div class="panel__head">
        <h2 class="panel__title">仿真模型</h2>
        <span class="panel__hint">前后端使用同一套公式</span>
      </div>
      <div class="panel__body model__body">
        <ul>
          <li><code>S_t = min(Q_t + A_t, C_t)</code> 本时段实际处理量</li>
          <li><code>Q_(t+1) = Q_t + A_t − S_t</code> 未处理积压结转</li>
          <li><code>P_t = min(D_t, I_t + S_t)</code> 实际取走量</li>
          <li><code>I_(t+1) = I_t + S_t − P_t</code> 待取库存结转</li>
          <li><code>Q_(t+1) + I_(t+1) = Q_t + I_t + A_t − P_t</code> 守恒校验</li>
        </ul>
        <p class="model__note">
          Q 未处理积压、I 已处理待取、A 到件、C 处理上限、D 取件需求、S/P 实际处理与实际取走。
          同一时段处理完的可当段取走；未满足的取件需求不结转，单列「未满足数」。
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.runs { display: flex; align-items: center; gap: var(--sp-2); font-size: var(--fs-xs); color: var(--fg-2); flex-wrap: wrap; }
.runs__select { padding: 4px var(--sp-2); background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-sm); color: var(--fg-0); font-size: var(--fs-xs); }
.runs__diff b { color: var(--fg-0); }
.runs__diff b.up { color: var(--danger-ink, var(--danger)); }
.runs__diff b.down { color: var(--ok-ink, var(--ok)); }

.pk { display: grid; gap: var(--sp-5); }

.pk__bar {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: var(--sp-4); flex-wrap: wrap;
}

.pk__site { display: inline-flex; gap: var(--sp-1); padding: var(--sp-1); background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-md); }
.chip {
  display: inline-flex; align-items: center; gap: var(--sp-1);
  padding: var(--sp-2) var(--sp-3); border-radius: var(--r-sm);
  font-size: var(--fs-sm); color: var(--fg-1);
}
.chip i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.chip:hover { background: var(--bg-3); color: var(--fg-0); }
.chip--on { background: var(--bg-4); color: var(--fg-0); font-weight: 600; }

.pk__summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--sp-3); }
.sum { display: grid; gap: 2px; padding: var(--sp-4) var(--sp-5); }
.sum__k { display: flex; align-items: center; gap: 4px; font-size: var(--fs-xs); color: var(--fg-2); }
.sum__v { font-size: var(--fs-xl); font-weight: 600; }
.sum__d { font-size: var(--fs-xs); color: var(--fg-2); }
.sum__d.up { color: var(--danger-ink); }
.sum__d.down { color: var(--ok-ink); }

.grid2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-5); }

.risk-list { border: 1px solid var(--line); border-radius: var(--r-md); overflow: hidden; }
.risk-head, .risk-row {
  display: grid; grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--sp-2); padding: var(--sp-2) var(--sp-3); font-size: var(--fs-xs);
}
.risk-head { background: var(--bg-3); color: var(--fg-1); font-weight: 600; border-bottom: 1px solid var(--line); }
.risk-scroll { max-height: 244px; overflow-y: auto; }
.risk-row { border-bottom: 1px solid var(--line); color: var(--fg-1); }
.risk-row:last-child { border-bottom: none; }
.num.hot { color: var(--danger-ink); font-weight: 600; }

.empty { font-size: var(--fs-sm); color: var(--fg-2); padding: var(--sp-6) 0; text-align: center; }

.model__body { display: grid; gap: var(--sp-3); }
.model__body ul { display: grid; gap: var(--sp-2); }
.model__body li { font-size: var(--fs-sm); color: var(--fg-1); }
.model__body code {
  font-family: 'JetBrains Mono', Consolas, ui-monospace, monospace;
  font-size: var(--fs-xs);
  background: var(--bg-2);
  padding: 1px 6px;
  border-radius: var(--r-sm);
  color: var(--brand);
}
.model__note { font-size: var(--fs-xs); color: var(--fg-2); line-height: var(--lh-loose); }

@media (max-width: 1200px) {
  .pk__summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .grid2 { grid-template-columns: 1fr; }
}
</style>
