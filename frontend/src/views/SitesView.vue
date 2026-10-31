<script setup lang="ts">
import { computed, ref } from 'vue'
import { MapPin, Clock, Package, Boxes, Layers, Info, ArrowRight } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import { useScenario } from '@/composables/useData'
import { SITES, SUPPLEMENTARY, NOT_TO_BUILD, isOpenNow } from '@/data/sites'
import StatusDot from '@/components/StatusDot.vue'
import ScenarioPicker from '@/components/ScenarioPicker.vue'
import SiteDrawer from '@/components/SiteDrawer.vue'
import { useReveal } from '@/composables/useReveal'

const store = useAppStore()
const scenario = useScenario(() => store.scenarioId)

const active = ref<string | null>(SITES[0].id)
const drawerOpen = ref(false)

const cards = computed(() =>
  SITES.map((s) => {
    const sum = scenario.value.summary.find((x) => x.site_id === s.id)!
    const params = scenario.value.sites.find((x) => x.site_id === s.id)!.params
    return { site: s, sum, params, open: isOpenNow(s) }
  })
)

const activeCard = computed(() => cards.value.find((c) => c.site.id === active.value) ?? cards.value[0])

const activeRows = computed(() => {
  const idx = scenario.value.sites.findIndex((s) => s.site_id === active.value)
  return scenario.value.timeline.map((t, i) => ({
    ...t.sites[idx],
    arrivals: scenario.value.sites[idx].demand[i].arrivals,
    capacity: scenario.value.sites[idx].demand[i].capacity,
    pickups: scenario.value.sites[idx].demand[i].pickups
  }))
})

useReveal(".sites > *, .panel")
</script>

<template>
  <div class="sv">
    <div class="sv__bar">
      <ScenarioPicker />
    </div>

    <section class="cards" aria-label="四个驿站">
      <button
        v-for="c in cards"
        :key="c.site.id"
        class="card"
        :class="{ 'card--on': active === c.site.id }"
        @click="active = c.site.id"
      >
        <span class="card__stripe" :style="{ background: c.site.color }" />
        <div class="card__top">
          <StatusDot :open="c.open" :risk="c.sum.risk_buckets > 0" />
          <h2 class="card__name">{{ c.site.shortName }}</h2>
          <span class="card__role">{{ c.site.roleLabel }}</span>
        </div>
        <p class="card__loc"><MapPin :size="12" /> {{ c.site.locationText }}</p>
        <p class="card__hours"><Clock :size="12" /> {{ c.site.hours.open }}—{{ c.site.hours.close }}</p>
        <div class="card__nums">
          <span><i class="num">{{ c.sum.daily_arrivals }}</i> 到件</span>
          <span><i class="num">{{ c.sum.peak_i }}</i> 峰值待取</span>
        </div>
        <span v-if="c.sum.risk_buckets" class="tag tag--danger">{{ c.sum.risk_buckets }} 个风险时段</span>
        <span v-else class="tag tag--ok">本场景无风险</span>
      </button>
    </section>

    <section class="detail">
      <div class="panel detail__main">
        <div class="panel__head">
          <h2 class="panel__title">
            {{ activeCard.site.name }}
            <span class="panel__hint">{{ activeCard.site.roleLabel }} · {{ activeCard.site.area }}</span>
          </h2>
          <button class="btn btn--ghost" @click="drawerOpen = true">
            打开详情抽屉 <ArrowRight :size="13" />
          </button>
        </div>

        <div class="panel__body detail__body">
          <dl class="spec">
            <div class="spec__item">
              <dt><Clock :size="13" /> 常态营业</dt>
              <dd class="num">{{ activeCard.site.hours.open }} — {{ activeCard.site.hours.close }}</dd>
              <span class="tag tag--public">公开资料</span>
            </div>
            <div class="spec__item">
              <dt><MapPin :size="13" /> 位置</dt>
              <dd>{{ activeCard.site.locationText }}</dd>
              <span class="tag tag--public">公开资料</span>
            </div>
            <div class="spec__item">
              <dt><Layers :size="13" /> 每时段处理上限 C</dt>
              <dd class="num">{{ activeCard.params.capacity_per_bucket }} 件</dd>
              <span class="tag tag--sim">模拟</span>
            </div>
            <div class="spec__item">
              <dt><Boxes :size="13" /> 积压上限 κ_q</dt>
              <dd class="num">{{ activeCard.params.kappa_q }} 件</dd>
              <span class="tag tag--sim">模拟</span>
            </div>
            <div class="spec__item">
              <dt><Package :size="13" /> 待取上限 κ_i</dt>
              <dd class="num">{{ activeCard.params.kappa_i }} 件</dd>
              <span class="tag tag--sim">模拟</span>
            </div>
            <div class="spec__item">
              <dt><Info :size="13" /> 实际库容 / 面积 / 货架数</dt>
              <dd class="unknown">待核实</dd>
              <span class="tag tag--unknown">无公开数据</span>
            </div>
          </dl>

          <div class="services">
            <h3>可办服务</h3>
            <ul>
              <li v-for="s in activeCard.site.services" :key="s">{{ s }}</li>
            </ul>
          </div>

          <div class="timeline">
            <h3>分时段运行表 <span class="panel__hint">30 分钟一桶</span></h3>
            <div class="tl">
              <div class="tl__head">
                <span>时段</span><span>到件</span><span>处理上限</span><span>取件需求</span><span>未处理积压</span><span>待取库存</span>
              </div>
              <div class="tl__scroll">
                <div
                  v-for="row in activeRows"
                  :key="row.bucket"
                  class="tl__row"
                  :class="{ 'tl__row--risk': row.risk_q || row.risk_i, 'tl__row--closed': row.capacity === 0 }"
                >
                  <span class="num">{{ row.bucket }}</span>
                  <span class="num">{{ row.arrivals }}</span>
                  <span class="num">{{ row.capacity }}</span>
                  <span class="num">{{ row.pickups }}</span>
                  <span class="num">{{ row.q }}</span>
                  <span class="num">{{ row.i }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <aside class="detail__side">
        <div class="panel">
          <div class="panel__head"><h2 class="panel__title">补充服务点</h2></div>
          <div class="panel__body side-body">
            <div v-for="s in SUPPLEMENTARY" :key="s.id" class="extra">
              <h3>{{ s.name }}</h3>
              <p>{{ s.locationText }}</p>
              <p class="extra__note">{{ s.note }}</p>
              <span class="tag tag--public">{{ s.tag }}</span>
            </div>
            <div class="extra extra--brand">
              <h3>顺丰驿收发 / 京东小蜜蜂</h3>
              <p>位于桃苑物流服务中心内西侧，为品牌自营服务区。</p>
              <p class="extra__note">不单独作为仿真站点，件量并入桃苑主站统计。</p>
              <span class="tag tag--public">公开资料</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel__head"><h2 class="panel__title">明确不建的站点</h2></div>
          <div class="panel__body side-body">
            <ul class="nots">
              <li v-for="n in NOT_TO_BUILD" :key="n">{{ n }}</li>
            </ul>
            <p class="side-note">没有可靠公开证据的地点，本项目不虚构为站点。</p>
          </div>
        </div>
      </aside>
    </section>

    <SiteDrawer v-model:open="drawerOpen" :site-id="active" :scenario="scenario" />
  </div>
</template>

<style scoped>
.sv { display: grid; gap: var(--sp-5); }

.cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--sp-3);
}

.card {
  position: relative;
  display: grid;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-5);
  text-align: left;
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  overflow: hidden;
  transition: border-color var(--t-fast) var(--ease), transform var(--t-fast) var(--ease);
}
.card:hover { transform: translateY(-2px); border-color: var(--line-strong); }
.card--on { border-color: var(--brand); box-shadow: 0 0 0 1px var(--brand-dim); }

.card__stripe { position: absolute; left: 0; top: 0; bottom: 0; width: 3px; }

.card__top { display: flex; align-items: center; gap: var(--sp-2); }
.card__name { font-size: var(--fs-md); }
.card__role { font-size: 10px; color: var(--fg-2); padding: 1px 6px; border: 1px solid var(--line); border-radius: var(--r-pill); }

.card__loc, .card__hours {
  display: flex; align-items: center; gap: 4px;
  font-size: var(--fs-xs); color: var(--fg-2);
}

.card__nums { display: flex; gap: var(--sp-4); font-size: var(--fs-xs); color: var(--fg-2); }
.card__nums i { font-style: normal; font-size: var(--fs-md); font-weight: 600; color: var(--fg-0); margin-right: 2px; }

.detail {
  display: grid;
  grid-template-columns: minmax(0, 2.1fr) minmax(280px, 1fr);
  gap: var(--sp-5);
  align-items: start;
}

.detail__body { display: grid; gap: var(--sp-5); }

.spec { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-2); }
.spec__item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px var(--sp-2);
  padding: var(--sp-3);
  background: var(--bg-2);
  border-radius: var(--r-md);
}
.spec__item dt { display: flex; align-items: center; gap: 4px; font-size: var(--fs-xs); color: var(--fg-2); grid-column: 1 / -1; }
.spec__item dd { margin: 0; font-size: var(--fs-sm); font-weight: 500; }
.spec__item .tag { justify-self: end; }
.unknown { color: var(--fg-2); font-style: italic; }

.services h3, .timeline h3 {
  font-size: var(--fs-sm);
  margin-bottom: var(--sp-2);
  display: flex; align-items: baseline; gap: var(--sp-2);
}
.services ul { display: grid; gap: var(--sp-1); }
.services li {
  font-size: var(--fs-sm);
  color: var(--fg-1);
  padding-left: var(--sp-4);
  position: relative;
}
.services li::before {
  content: '';
  position: absolute; left: 6px; top: 9px;
  width: 4px; height: 4px; border-radius: 50%;
  background: var(--brand);
}

.tl { border: 1px solid var(--line); border-radius: var(--r-md); overflow: hidden; }
.tl__head, .tl__row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  font-size: var(--fs-xs);
}
.tl__head {
  background: var(--bg-3);
  color: var(--fg-1);
  font-weight: 600;
  border-bottom: 1px solid var(--line);
}
.tl__scroll { max-height: 300px; overflow-y: auto; }
.tl__row { border-bottom: 1px solid var(--line); color: var(--fg-1); }
.tl__row:last-child { border-bottom: none; }
.tl__row--risk { background: var(--danger-dim); color: var(--fg-0); }
.tl__row--closed { opacity: 0.45; }

.side-body { display: grid; gap: var(--sp-4); }
.extra { display: grid; gap: var(--sp-1); }
.extra h3 { font-size: var(--fs-sm); }
.extra p { font-size: var(--fs-xs); color: var(--fg-1); line-height: var(--lh-loose); }
.extra__note { color: var(--fg-2) !important; }
.extra .tag { justify-self: start; margin-top: var(--sp-1); }
.extra--brand { padding-top: var(--sp-4); border-top: 1px dashed var(--line-strong); }

.nots { display: grid; gap: var(--sp-2); }
.nots li {
  font-size: var(--fs-xs);
  color: var(--fg-1);
  padding-left: var(--sp-4);
  position: relative;
  line-height: var(--lh-loose);
}
.nots li::before {
  content: '×';
  position: absolute; left: 4px; top: 0;
  color: var(--danger-ink);
  font-weight: 700;
}

.side-note { font-size: var(--fs-xs); color: var(--fg-2); margin-top: var(--sp-3); }

.btn {
  display: inline-flex; align-items: center; gap: var(--sp-1);
  height: 30px; padding: 0 var(--sp-3);
  border-radius: var(--r-md); font-size: var(--fs-xs);
}
.btn--ghost { border: 1px solid var(--line); color: var(--fg-1); }
.btn--ghost:hover { background: var(--bg-2); color: var(--fg-0); }

@media (max-width: 1300px) {
  .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .detail { grid-template-columns: 1fr; }
}
@media (max-width: 700px) {
  .cards { grid-template-columns: 1fr; }
  .spec { grid-template-columns: 1fr; }
}
</style>
