<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Package, PackageCheck, Layers, Boxes, TriangleAlert, PackageX, ArrowUpRight, Maximize2 } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import { useScenario, scenarioKpi, simSeries } from '@/composables/useData'
import { SITES, isOpenNow } from '@/data/sites'
import { useChartTheme } from '@/composables/useChartTheme'
import KpiCard from '@/components/KpiCard.vue'
import StatusDot from '@/components/StatusDot.vue'
import CampusMap from '@/components/CampusMap.vue'
import MapExpand from '@/components/MapExpand.vue'
import EChart from '@/components/EChart.vue'
import ScenarioPicker from '@/components/ScenarioPicker.vue'
import SiteDrawer from '@/components/SiteDrawer.vue'
import PickupLookup from '@/components/PickupLookup.vue'
import { getCarrierStats, type CarrierStat } from '@/data/mysql'
import { onMounted } from 'vue'
import { useReveal } from '@/composables/useReveal'

const store = useAppStore()
const router = useRouter()
const scenario = useScenario(() => store.scenarioId)
const kpi = computed(() => scenarioKpi(scenario.value))
const { t, tooltip, axisCommon } = useChartTheme()

const selected = ref<string | null>(null)
const mapBig = ref(false)
const drawerOpen = ref(false)

function pickSite(id: string) {
  selected.value = id
  drawerOpen.value = true
}

const openMap = computed(() =>
  Object.fromEntries(SITES.map((s) => [s.id, isOpenNow(s)]))
)

const riskMap = computed(() =>
  Object.fromEntries(scenario.value.summary.map((s) => [s.site_id, s.risk_buckets > 0]))
)

// 全站到件/取件曲线
const flowOption = computed(() => {
  const buckets = scenario.value.timeline.map((x) => x.bucket)
  // 到件量取自 demand，处理/取走量取自仿真结果
  const A = scenario.value.timeline.map((x, i) =>
    scenario.value.sites.reduce((a, site) => a + site.demand[i].arrivals, 0)
  )
  const S = scenario.value.timeline.map((x) => x.sites.reduce((a, r) => a + r.s, 0))
  const P = scenario.value.timeline.map((x) => x.sites.reduce((a, r) => a + r.p, 0))


  return {
    grid: { left: 44, right: 16, top: 34, bottom: 30 },
    tooltip: { trigger: 'axis', ...tooltip.value, axisPointer: { type: 'line', lineStyle: { color: t.value.axis } } },
    legend: {
      top: 0, right: 0, icon: 'roundRect', itemWidth: 9, itemHeight: 9, itemGap: 14,
      textStyle: { color: t.value.text, fontSize: 11 }
    },
    xAxis: {
      type: 'category', data: buckets, boundaryGap: false, ...axisCommon.value,
      splitLine: { show: false },
      axisLabel: { color: t.value.text, fontSize: 10, interval: 3 }
    },
    yAxis: { type: 'value', ...axisCommon.value, name: '件', nameTextStyle: { color: t.value.text, fontSize: 10 } },
    series: [
      {
        name: '到件', type: 'line', data: A, smooth: 0.3, symbol: 'none',
        lineStyle: { width: 2, color: t.value.series[0] },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(232,163,61,0.28)' },
              { offset: 1, color: 'rgba(232,163,61,0)' }
            ]
          }
        }
      },
      {
        name: '已处理', type: 'line', data: S, smooth: 0.3, symbol: 'none',
        lineStyle: { width: 2, color: t.value.series[1] }
      },
      {
        name: '已取走', type: 'line', data: P, smooth: 0.3, symbol: 'none',
        lineStyle: { width: 1.5, color: t.value.series[2], type: 'dashed' }
      }
    ]
  }
})

const fmt = (n: number) => n.toLocaleString('zh-CN')

/** 取某站的库容上限，用于算占用率 */
function siteKappaI(siteId: string) {
  return scenario.value.sites.find((s) => s.site_id === siteId)?.params.kappa_i ?? 1
}
function siteKappaQ(siteId: string) {
  return scenario.value.sites.find((s) => s.site_id === siteId)?.params.kappa_q ?? 1
}

const carriers = ref<CarrierStat[]>([])
const maxCarrier = computed(() => Math.max(1, ...carriers.value.map((c) => c.onShelf)))

onMounted(async () => {
  const list = await getCarrierStats('NH-TAOYUAN')
  if (list) carriers.value = list
})

const weekRows = computed(() => {
  const wk = scenario.value.week ?? []
  return wk.map((d) => {
    const t = d.sites.find((s) => s.site_id === 'NH-TAOYUAN') ?? d.sites[0]
    return {
      day: d.day,
      pct: t.occupancy_pct,
      level: t.level,
      projected: t.projected,
      h: Math.min(100, t.occupancy_pct)
    }
  })
})


void simSeries

useReveal(".kpis > *, .ov__main > *, .ov__charts > *")
</script>

<template>
  <div class="ov">
    <div class="ov__bar">
      <ScenarioPicker />
      <RouterLink to="/peak" class="link-btn">
        查看高峰方案 <ArrowUpRight :size="14" />
      </RouterLink>
    </div>

    <section class="kpis" aria-label="关键指标">
      <KpiCard label="当日到件" :value="kpi.totalArrivals" unit="件" :icon="Package" simulated hint="四站合计，演示假设" />
      <KpiCard label="当日取走" :value="kpi.totalPickups" unit="件" :icon="PackageCheck" simulated hint="实际完成取件，不含未满足" />
      <KpiCard label="最高占用率" :value="kpi.maxOcc" unit="%" :icon="Boxes" simulated
        :tone="kpi.maxOcc >= 85 ? 'danger' : kpi.maxOcc >= 70 ? 'warn' : 'ok'"
        hint="物理储位占用，最高的站点" />
      <KpiCard label="通道可通行率" :value="kpi.minAisle" unit="%" :icon="Layers" simulated
        :tone="kpi.minAisle < 70 ? 'danger' : kpi.minAisle < 85 ? 'warn' : 'ok'"
        hint="低于 70% 即通道受限" />
      <KpiCard label="高峰排队" :value="kpi.maxQueue" unit="分钟" :icon="TriangleAlert" simulated
        :tone="kpi.maxQueue > 20 ? 'danger' : kpi.maxQueue > 10 ? 'warn' : 'ok'"
        hint="超过 20 分钟即服务受限" />
      <KpiCard label="未满足取件" :value="kpi.unmet" unit="件" :icon="PackageX" simulated
        :tone="kpi.unmet > 0 ? 'danger' : 'ok'" hint="需求超过可交付量" />
    </section>

    <section class="ov__main">
      <div class="panel ov__map">
        <div class="panel__head">
          <h2 class="panel__title">南湖校区站点分布</h2>
          <button class="btn btn--ghost map-expand" @click="mapBig = true">
            <Maximize2 :size="13" /> 放大
          </button>
        </div>
        <CampusMap :scenario="scenario" :selected-id="selected" @select="pickSite" />

        <MapExpand v-model:open="mapBig" :scenario="scenario" :selected-id="selected" @select="pickSite" />
      </div>

      <div class="ov__side">
        <div class="panel ov__pickup">
          <div class="panel__head">
            <h2 class="panel__title">取件码查询</h2>
            <span class="panel__hint">查位置与承运商</span>
          </div>
          <div class="panel__body">
            <PickupLookup />
          </div>
        </div>

        <div v-if="carriers.length" class="panel ov__carrier">
          <div class="panel__head">
            <h2 class="panel__title">在架件按承运商</h2>
            <span class="panel__hint">桃苑 · 当前在架</span>
          </div>
          <div class="panel__body">
            <ul class="carrier__list">
              <li v-for="c in carriers" :key="c.carrierCode">
                <span class="carrier__name">{{ c.carrier }}</span>
                <span class="carrier__track">
                  <i :style="{ width: (c.onShelf / maxCarrier) * 100 + '%' }" />
                </span>
                <span class="carrier__num num">{{ c.onShelf }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section class="ov__flowrow">
      <div class="panel">
        <div class="panel__head">
          <h2 class="panel__title">全站流量曲线</h2>
          <span class="panel__hint">30 分钟一桶 · 到件 / 已处理 / 已取走</span>
        </div>
        <div class="panel__body">
          <EChart :option="flowOption" :height="240" />
        </div>
      </div>

      <div class="panel">
        <div class="panel__head">
          <h2 class="panel__title">本周与推演</h2>
          <span class="panel__hint">第 7 天按设计占用率回推，第 8—9 天为外推</span>
        </div>
        <div class="panel__body">
          <ol class="week">
            <li v-for="d in weekRows" :key="d.day" class="week__item" :class="'week__item--' + d.level">
              <span class="week__day">D{{ d.day }}</span>
              <span class="week__bar"><i :style="{ height: d.h + '%' }" /></span>
              <span class="week__num num">{{ d.pct }}%</span>
              <span v-if="d.projected" class="week__proj">外推</span>
            </li>
          </ol>

          <p class="note">
            第 7 天收盘 {{ weekRows[6]?.pct }}%，仍在运营上限（物理储位的 85%）之下；
            按每天净增 {{ fmt(scenario.summary[0]?.net_per_day ?? 0) }} 件推算，第 9 天会越过满仓线。
          </p>
        </div>
      </div>
    </section>



    <SiteDrawer v-model:open="drawerOpen" :site-id="selected" :scenario="scenario" @go-sites="router.push('/sites')" />
  </div>
</template>

<style scoped>
.ov__charts--single { grid-template-columns: minmax(0, 1fr); }
/* 地图按 1.62:1 的原图比例给高度，避免上下大片黑边 */
.ov__map :deep(.map) { min-height: 400px; height: clamp(360px, 34vw, 460px); }
.ov__side { display: grid; gap: var(--sp-4); align-content: start; }
.ov__flowrow {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: var(--sp-4);
  margin-top: var(--sp-4);
}
@media (max-width: 1100px) {
  .ov__flowrow { grid-template-columns: minmax(0, 1fr); }
}
.ov__carrier .carrier__list { display: grid; gap: 6px; }
.ov__carrier .carrier__list li {
  display: grid;
  grid-template-columns: 62px minmax(0, 1fr) 46px;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--fs-xs);
}
.ov__carrier .carrier__name { color: var(--fg-2); }
.ov__carrier .carrier__track {
  height: 12px;
  border-radius: 2px;
  background: var(--bg-2);
  overflow: hidden;
}
.ov__carrier .carrier__track i {
  display: block;
  height: 100%;
  border-radius: 2px;
  background: color-mix(in oklab, var(--brand) 55%, transparent);
}
.ov__carrier .carrier__num { text-align: right; color: var(--fg-1); }

.map-expand { margin-left: auto; font-size: var(--fs-xs); }
/* 面板是 grid 且默认 stretch，行高会被右栏撑开；这里把表头钉死，剩下的都给地图 */
.ov__map { grid-template-rows: auto minmax(0, 1fr); align-self: start; }

.carrier { display: grid; gap: 6px; margin: var(--sp-3) 0; }
.carrier__title { font-size: var(--fs-xs); color: var(--fg-2); }
.carrier__list { display: grid; gap: 4px; }
.carrier__list li { display: grid; grid-template-columns: 64px minmax(0, 1fr) 48px; align-items: center; gap: var(--sp-2); position: relative; font-size: var(--fs-xs); }
.carrier__bar { position: absolute; left: 64px; height: 12px; background: var(--brand-dim); border-radius: 2px; z-index: 0; }
.carrier__name { grid-column: 1; color: var(--fg-3, var(--fg-2)); }
.carrier__num { grid-column: 3; text-align: right; color: var(--fg-1); }

.week { display: flex; align-items: flex-end; gap: 8px; height: 132px; margin-bottom: var(--sp-3); }
.week__item { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1 1 0; height: 100%; }
.week__day { font-size: 10px; color: var(--fg-2); }
.week__bar { flex: 1 1 auto; width: 100%; display: flex; align-items: flex-end; background: var(--bg-2); border-radius: 3px; overflow: hidden; }
.week__bar i { display: block; width: 100%; background: var(--ok); transition: height 0.3s var(--ease); }
.week__item--watch .week__bar i { background: var(--warn); }
.week__item--limit .week__bar i { background: var(--danger); }
.week__item--overflow .week__bar i { background: var(--danger); filter: brightness(0.8); }
.week__num { font-size: 10px; color: var(--fg-1); }
.week__proj { font-size: 9px; color: var(--fg-2); }

.ov { display: grid; gap: var(--sp-5); }

.ov__bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
}

.link-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--bg-1);
  font-size: var(--fs-sm);
  color: var(--fg-1);
  transition: background var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
}
.link-btn:hover { background: var(--bg-2); color: var(--fg-0); }

.kpis {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--sp-3);
}

.ov__main {
  display: grid;
  grid-template-columns: minmax(0, 1.06fr) minmax(360px, 1fr);
  gap: var(--sp-5);
  align-items: stretch;
}

.ov__side { display: grid; gap: var(--sp-4); grid-template-rows: auto 1fr; }

.ov__map { display: grid; }
.ov__map :deep(.map-wrap) { border: none; border-radius: 0 0 var(--r-lg) var(--r-lg); }

.site-list { padding: var(--sp-2) var(--sp-2) 0; display: grid; gap: 2px; }

.site-row {
  display: grid;
  grid-template-columns: 3px 14px minmax(84px, 1fr) auto auto auto;
  align-items: center;
  gap: var(--sp-2);
  width: 100%;
  padding: var(--sp-3) var(--sp-2);
  border-radius: var(--r-md);
  text-align: left;
  transition: background var(--t-fast) var(--ease);
}
.site-row:hover { background: var(--bg-2); }

.site-row__bar { width: 3px; height: 22px; border-radius: var(--r-pill); }

.site-row__name { font-weight: 600; font-size: var(--fs-base); display: flex; align-items: baseline; gap: var(--sp-1); }
.site-row__name em { font-style: normal; font-size: 10px; font-weight: 400; color: var(--fg-2); }

.site-row__num { font-size: var(--fs-md); font-weight: 600; }
.site-row__unit { font-size: 10px; color: var(--fg-2); white-space: nowrap; }

.site-list__note {
  padding: var(--sp-3) var(--sp-4) var(--sp-4);
  font-size: var(--fs-xs);
  color: var(--fg-2);
  line-height: var(--lh-loose);
}

.ov__charts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sp-5);
}


@media (max-width: 1400px) {
  .kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 1100px) {
  .ov__main { grid-template-columns: 1fr; }
  .ov__charts { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
