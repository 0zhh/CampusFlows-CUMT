<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Package, PackageCheck, Layers, Boxes, TriangleAlert, PackageX, ArrowUpRight } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import { useScenario, scenarioKpi, simSeries } from '@/composables/useData'
import { SITES, isOpenNow } from '@/data/sites'
import { useChartTheme } from '@/composables/useChartTheme'
import KpiCard from '@/components/KpiCard.vue'
import StatusDot from '@/components/StatusDot.vue'
import CampusMap from '@/components/CampusMap.vue'
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

// 四站负荷对比（峰值积压 vs 上限）
const loadOption = computed(() => {
  const names = scenario.value.summary.map((s) => SITES.find((x) => x.id === s.site_id)?.shortName ?? s.site_id)
  const peakQ = scenario.value.summary.map((s) => s.peak_q)
  const kapQ = scenario.value.summary.map((s) => scenario.value.sites.find((x) => x.site_id === s.site_id)!.params.kappa_q)
  return {
    grid: { left: 44, right: 16, top: 30, bottom: 26 },
    tooltip: { trigger: 'axis', ...tooltip.value, axisPointer: { type: 'shadow' } },
    legend: { top: 0, right: 0, icon: 'roundRect', itemWidth: 9, itemHeight: 9, textStyle: { color: t.value.text, fontSize: 11 } },
    xAxis: { type: 'category', data: names, ...axisCommon.value, splitLine: { show: false } },
    yAxis: { type: 'value', ...axisCommon.value, name: '件', nameTextStyle: { color: t.value.text, fontSize: 10 } },
    series: [
      {
        name: '峰值积压', type: 'bar', data: peakQ, barWidth: '38%',
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: (p: any) => (peakQ[p.dataIndex] > kapQ[p.dataIndex] ? '#e2605a' : '#3ec9a7')
        }
      },
      {
        name: '积压上限 κ_q', type: 'line', data: kapQ, symbol: 'none',
        lineStyle: { width: 1.5, type: 'dashed', color: t.value.series[0] }
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

/** 本期要点：完全由当前场景数据推导，不写死文案 */
const brief = computed(() => {
  const sc = scenario.value
  const riskSites = sc.summary.filter((s) => s.risk_buckets > 0)
  const worst = [...sc.summary].sort((a, b) => b.peak_q - a.peak_q)[0]
  const worstSite = SITES.find((s) => s.id === worst.site_id)
  const items: { title: string; text: string; tone: string }[] = []

  if (riskSites.length === 0) {
    items.push({
      title: '全程无风险',
      text: `四个站点在所有 ${sc.timeline.length} 个时段内，未处理积压与待取库存都未越过阈值。`,
      tone: 'ok'
    })
  } else {
    const first = riskSites
      .map((s) => s.first_risk_bucket)
      .filter(Boolean)
      .sort()[0]
    items.push({
      title: `${riskSites.length} 个站点出现风险`,
      text: `最早在 ${first} 越过阈值，合计 ${fmt(riskSites.reduce((a, s) => a + s.risk_buckets, 0))} 个风险时段。`,
      tone: 'danger'
    })
  }

  if (worst.peak_q > siteKappaQ(worst.site_id) * 0.05) {
    // 第二名的峰值，用来说明"头部有多集中"
    const ranked = [...sc.summary].sort((a, b) => b.peak_q - a.peak_q)
    const second = ranked[1]
    const lead = second && second.peak_q > 0
      ? `，是第二名${SITES.find((s) => s.id === second.site_id)?.shortName ?? ''}（${fmt(second.peak_q)} 件）的 ${(worst.peak_q / second.peak_q).toFixed(1)} 倍`
      : '，其余站点本场景基本无积压'
    items.push({
      title: `压力集中在${worstSite?.shortName ?? '—'}`,
      text: `峰值积压 ${fmt(worst.peak_q)} 件${lead}；峰值待取 ${fmt(worst.peak_i)} 件。`,
      tone: 'warn'
    })
  } else if (worst.peak_q > 0) {
    // 有积压但远没到风险线：说明离阈值还有多远
    const run = Math.round((1 - worst.peak_q / siteKappaQ(worst.site_id)) * 100)
    items.push({
      title: `${worstSite?.shortName ?? '—'}积压最重，但仍在阈值内`,
      text: `峰值积压 ${fmt(worst.peak_q)} 件，距 ${fmt(siteKappaQ(worst.site_id))} 件的积压上限还有 ${run}% 余量。`,
      tone: 'ok'
    })
  } else {
    // 积压基本为零：不谈"压力集中"，改看谁最接近待取区上限
    const tight = [...sc.summary].sort(
      (a, b) => b.peak_i / siteKappaI(b.site_id) - a.peak_i / siteKappaI(a.site_id)
    )[0]
    const tightName = SITES.find((s) => s.id === tight.site_id)?.shortName ?? '—'
    const used = Math.round((tight.peak_i / siteKappaI(tight.site_id)) * 100)
    items.push({
      title: '积压已压到接近于零',
      text: `四站峰值积压合计不足阈值的 5%。最接近上限的是${tightName}的待取区：峰值 ${fmt(tight.peak_i)} 件，占用 ${used}%。`,
      tone: used > 85 ? 'warn' : 'ok'
    })
  }

  if (kpi.value.unmet > 0) {
    items.push({
      title: '存在未满足取件',
      text: `全天 ${fmt(kpi.value.unmet)} 件取件需求超出现场可交付量，需引导错峰或延长服务。`,
      tone: 'warn'
    })
  } else {
    items.push({
      title: '取件需求全部满足',
      text: '各时段取件需求均未超过待取库存，无用户白跑一趟的情况。',
      tone: 'ok'
    })
  }

  return items
})

const siteRows = computed(() =>
  SITES.map((s) => {
    const sum = scenario.value.summary.find((x) => x.site_id === s.id)!
    return { site: s, sum, open: openMap.value[s.id], risk: riskMap.value[s.id] }
  })
)

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

function levelText(l?: string) {
  return l === 'overflow' ? '满仓' : l === 'limit' ? '限流' : l === 'watch' ? '预警' : '正常'
}
function levelTag(l?: string) {
  return l === 'overflow' || l === 'limit' ? 'tag--danger' : l === 'watch' ? 'tag--warn' : 'tag--ok'
}

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
          <span class="panel__hint">点击站点查看当前负荷</span>
        </div>
        <CampusMap :scenario="scenario" :selected-id="selected" @select="pickSite" />
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

        <div class="panel ov__sites">
          <div class="panel__head">
            <h2 class="panel__title">四站实时状态</h2>
            <RouterLink to="/sites" class="panel__hint">全部站点 →</RouterLink>
          </div>
          <ul class="site-list">
            <li v-for="r in siteRows" :key="r.site.id">
              <button class="site-row" @click="pickSite(r.site.id)">
                <span class="site-row__bar" :style="{ background: r.site.color }" />
                <StatusDot :open="r.open" :risk="r.risk" />
                <span class="site-row__name">
                  {{ r.site.shortName }}
                  <em>{{ r.site.roleLabel }}</em>
                </span>
                <span class="site-row__num num">{{ r.sum.peak_q }}</span>
                <span class="site-row__unit">件</span>
                <span class="tag" :class="levelTag(r.sum.level)">{{ levelText(r.sum.level) }}</span>
              </button>
            </li>
          </ul>
          <p class="site-list__note">
            营业状态按常态时间实时计算；业务数值为演示假设，营业时间与位置来自公开资料。
          </p>
        </div>

        <div class="panel ov__flow">
          <div class="panel__head">
            <h2 class="panel__title">全站流量曲线</h2>
            <span class="panel__hint">30 分钟一桶</span>
          </div>
          <div class="panel__body">
            <EChart :option="flowOption" :height="248" />
          </div>
        </div>
      </div>
    </section>

    <section class="ov__charts">
      <div class="panel">
        <div class="panel__head">
          <h2 class="panel__title">各站峰值积压 vs 上限</h2>
          <span class="panel__hint">超过 κ_q 即为风险</span>
        </div>
        <div class="panel__body">
          <EChart :option="loadOption" :height="260" />
        </div>
      </div>

      <div class="panel">
        <div class="panel__head">
          <h2 class="panel__title">本期要点</h2>
          <span class="panel__hint">随场景自动变化</span>
        </div>
        <div class="panel__body">
          <ul class="brief">
            <li v-for="(b, i) in brief" :key="i" :class="'brief--' + b.tone">
              <b>{{ b.title }}</b>
              <span>{{ b.text }}</span>
            </li>
          </ul>
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
          <div v-if="carriers.length" class="carrier">
            <span class="carrier__title">在架件按承运商</span>
            <ul class="carrier__list">
              <li v-for="c in carriers" :key="c.carrierCode">
                <i class="carrier__bar" :style="{ width: (c.onShelf / maxCarrier) * 100 + '%' }" />
                <span class="carrier__name">{{ c.carrier }}</span>
                <span class="carrier__num num">{{ c.onShelf }}</span>
              </li>
            </ul>
          </div>

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

.brief { display: grid; gap: var(--sp-3); }
.brief li {
  display: grid;
  gap: 2px;
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--r-md);
  background: var(--bg-2);
  border-left: 3px solid var(--line-strong);
}
.brief--ok { border-left-color: var(--ok) !important; }
.brief--warn { border-left-color: var(--warn) !important; }
.brief--danger { border-left-color: var(--danger) !important; }
.brief b { font-size: var(--fs-sm); }
.brief span { font-size: var(--fs-xs); color: var(--fg-1); line-height: var(--lh-loose); }

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
