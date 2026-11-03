<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Siren, Clock, CheckCircle2, CircleDot, RotateCcw, ChevronRight, User, Bot } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import { useScenario } from '@/composables/useData'
import { SITES } from '@/data/sites'
import { generateIncidents, type Incident, type IncidentStatus } from '@/data/incidents'
import ScenarioPicker from '@/components/ScenarioPicker.vue'
import { useReveal } from '@/composables/useReveal'
import { fetchWorkOrders, patchWorkOrder, resetWorkOrders, toStatusMap } from '@/data/workOrders'

const store = useAppStore()
const scenario = useScenario(() => store.scenarioId)

/** 本地可变的工单副本；接后端后改为 PATCH /api/incidents/{id} */
const overrides = ref<Record<string, IncidentStatus>>({})
const incidents = computed<Incident[]>(() =>
  generateIncidents(scenario.value).map((i) => ({ ...i, status: overrides.value[i.id] ?? i.status }))
)

const statusFilters: { id: 'all' | IncidentStatus; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: 'open', label: '待处理' },
  { id: 'doing', label: '处理中' },
  { id: 'closed', label: '已闭环' }
]
const filter = ref<'all' | IncidentStatus>('all')

const STATUS_RANK: Record<string, number> = { open: 0, doing: 1, closed: 2 }

/** 未闭环的排前面，同状态按风险时段先后 */
/** 只在生成时按状态排一次；点击改状态不重排，避免列表在脚下跳动 */
const filtered = computed(() =>
  filter.value === 'all' ? incidents.value : incidents.value.filter((i) => i.status === filter.value)
)

const current = ref<string | null>(null)
const currentIncident = computed(
  () => incidents.value.find((i) => i.id === current.value) ?? filtered.value[0] ?? null
)

const counts = computed(() => ({
  all: incidents.value.length,
  open: incidents.value.filter((i) => i.status === 'open').length,
  doing: incidents.value.filter((i) => i.status === 'doing').length,
  closed: incidents.value.filter((i) => i.status === 'closed').length
}))

/** 后端可用时，工单状态写回数据库；不可用时只改本地 */
const apiMode = computed(() => store.dataMode === 'api')

onMounted(async () => {
  if (!apiMode.value) return
  const remote = await fetchWorkOrders()
  if (remote) overrides.value = { ...overrides.value, ...toStatusMap(remote) }
})

function setStatus(id: string, s: IncidentStatus) {
  overrides.value = { ...overrides.value, [id]: s }
  if (apiMode.value) void patchWorkOrder(id, s)
}

function reset() {
  overrides.value = {}
  current.value = null
  if (apiMode.value) void resetWorkOrders()
}

function siteOf(id: string) {
  return SITES.find((s) => s.id === id)
}

const statusMeta: Record<IncidentStatus, { label: string; cls: string; icon: any }> = {
  open: { label: '待处理', cls: 'tag--danger', icon: CircleDot },
  doing: { label: '处理中', cls: 'tag--sim', icon: Clock },
  closed: { label: '已闭环', cls: 'tag--ok', icon: CheckCircle2 }
}

useReveal(".stat, .wo, .panel")
</script>

<template>
  <div class="iv">
    <div class="iv__bar">
      <ScenarioPicker />
      <button class="btn btn--ghost" @click="reset">
        <RotateCcw :size="13" /> 复位工单状态
      </button>
      <span class="tag" :class="apiMode ? 'tag--public' : 'tag--sim'">
        {{ apiMode ? '状态写入后端数据库' : '演示数据模式（状态仅在本机）' }}
      </span>
    </div>

    <section class="iv__stats">
      <button
        v-for="f in statusFilters"
        :key="f.id"
        class="stat"
        :class="{ 'stat--on': filter === f.id }"
        @click="filter = f.id"
      >
        <span class="stat__n num">{{ counts[f.id] }}</span>
        <span class="stat__l">{{ f.label }}</span>
      </button>
      <div class="stat stat--info">
        <span class="stat__n num">{{ incidents.filter((i) => i.level === 'high').length }}</span>
        <span class="stat__l">高优先级</span>
      </div>
      <div class="stat stat--info">
        <span class="stat__n num">{{ incidents.filter((i) => i.kind === 'watch').length }}</span>
        <span class="stat__l">预警（未越限）</span>
      </div>
    </section>

    <section class="iv__main">
      <div class="panel list">
        <div class="panel__head">
          <h2 class="panel__title"><Siren :size="15" /> 风险工单</h2>
          <span class="panel__hint">由仿真风险时段自动生成</span>
        </div>
        <ul class="list__body">
          <li v-for="i in filtered" :key="i.id">
            <button
              class="wo"
              :class="{ 'wo--on': currentIncident?.id === i.id }"
              @click="current = i.id"
            >
              <span class="wo__level" :class="'wo__level--' + i.level" />
              <span class="wo__main">
                <span class="wo__title">
                  {{ i.title }}
                  <span v-if="i.kind !== 'exceed'" class="wo__kind" :class="'wo__kind--' + i.kind">
                    {{ i.kind === 'watch' ? '预警' : '演练' }}
                  </span>
                </span>
                <span class="wo__meta">
                  {{ i.id }} · {{ i.bucket }} · {{ siteOf(i.siteId)?.roleLabel }}
                </span>
              </span>
              <span class="tag" :class="statusMeta[i.status].cls">{{ statusMeta[i.status].label }}</span>
              <ChevronRight :size="14" class="wo__arrow" />
            </button>
          </li>
          <li v-if="!filtered.length" class="list__empty">当前筛选下没有工单</li>
        </ul>
      </div>

      <div v-if="currentIncident" class="panel detail">
        <div class="panel__head">
          <h2 class="panel__title">{{ currentIncident.title }}</h2>
          <span class="tag" :class="statusMeta[currentIncident.status].cls">
            {{ statusMeta[currentIncident.status].label }}
          </span>
        </div>
        <div class="panel__body detail__body">
          <div class="kv">
            <div><span>工单号</span><b class="num">{{ currentIncident.id }}</b></div>
            <div><span>站点</span><b>{{ siteOf(currentIncident.siteId)?.name }}</b></div>
            <div><span>触发时段</span><b class="num">{{ currentIncident.bucket }}</b></div>
            <div><span>优先级</span><b>{{ currentIncident.level === 'high' ? '高' : currentIncident.level === 'mid' ? '中' : '低' }}</b></div>
          </div>

          <div class="block">
            <h3>触发指标</h3>
            <p class="metric-line">{{ currentIncident.metric }}</p>
            <span class="tag tag--sim">模拟</span>
          </div>

          <div class="block">
            <h3>风险说明</h3>
            <p>{{ currentIncident.detail }}</p>
          </div>

          <div class="block">
            <h3>处理记录</h3>
            <ol class="tl">
              <li v-for="(a, idx) in currentIncident.actions" :key="idx">
                <span class="tl__dot" />
                <div class="tl__card">
                  <div class="tl__head">
                    <span class="tl__by">
                      <Bot v-if="a.by === '系统'" :size="12" />
                      <User v-else :size="12" />
                      {{ a.by }}
                    </span>
                    <span class="tl__at num">{{ a.at }}</span>
                  </div>
                  <p>{{ a.text }}</p>
                </div>
              </li>
            </ol>
          </div>

          <div class="block actions">
            <h3>状态流转</h3>
            <div class="actions__row">
              <button
                class="btn"
                :class="currentIncident.status === 'open' ? 'btn--primary' : 'btn--ghost'"
                @click="setStatus(currentIncident.id, 'open')"
              >待处理</button>
              <button
                class="btn"
                :class="currentIncident.status === 'doing' ? 'btn--primary' : 'btn--ghost'"
                @click="setStatus(currentIncident.id, 'doing')"
              >处理中</button>
              <button
                class="btn"
                :class="currentIncident.status === 'closed' ? 'btn--primary' : 'btn--ghost'"
                @click="setStatus(currentIncident.id, 'closed')"
              >已闭环</button>
            </div>
            <p class="actions__note">演示用：状态仅保存在浏览器内存，刷新页面即复位。接后端后写入数据库。</p>
          </div>
        </div>
      </div>

      <div v-else class="panel detail detail--empty">
        <p>当前筛选下没有可显示的工单。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.iv { display: grid; gap: var(--sp-5); }

.iv__bar { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-4); flex-wrap: wrap; }

.iv__stats { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.stat {
  display: grid; gap: 1px; min-width: 96px;
  padding: var(--sp-3) var(--sp-4);
  background: var(--bg-1); border: 1px solid var(--line);
  border-radius: var(--r-md); text-align: left;
  transition: border-color var(--t-fast) var(--ease);
}
.stat:hover { border-color: var(--line-strong); }
.stat--on { border-color: var(--brand); background: var(--brand-dim); }
.stat--info { cursor: default; }
.stat__n { font-size: var(--fs-lg); font-weight: 600; }
.stat__l { font-size: var(--fs-xs); color: var(--fg-2); }

.iv__main { display: grid; grid-template-columns: minmax(320px, 0.85fr) minmax(0, 1.4fr); gap: var(--sp-5); align-items: start; }

.list__body { padding: var(--sp-2); display: grid; gap: 2px; }
.list__empty { padding: var(--sp-6); text-align: center; color: var(--fg-2); font-size: var(--fs-sm); }

.wo {
  display: grid;
  grid-template-columns: 3px minmax(0, 1fr) auto 14px;
  align-items: center;
  gap: var(--sp-3);
  width: 100%;
  padding: var(--sp-3);
  border-radius: var(--r-md);
  text-align: left;
  transition: background var(--t-fast) var(--ease);
}
.wo:hover { background: var(--bg-2); }
.wo--on { background: var(--bg-3); }

.wo__level { width: 3px; height: 30px; border-radius: var(--r-pill); background: var(--fg-2); }
.wo__level--high { background: var(--danger); }
.wo__level--mid { background: var(--warn); }
.wo__level--low { background: var(--info); }

.wo__main { display: grid; gap: 2px; min-width: 0; }
.wo__title { font-size: var(--fs-sm); font-weight: 600; display: flex; align-items: center; gap: var(--sp-2); }
.wo__kind {
  font-size: 10px;
  font-weight: 500;
  padding: 0 6px;
  border-radius: var(--r-pill);
  color: var(--info-ink);
  background: var(--info-dim);
  border: 1px dashed rgb(91 155 213 / 0.4);
}
.wo__kind--drill { color: var(--fg-2); background: var(--bg-3); border-color: var(--line-strong); }
.wo__meta { font-size: 10px; color: var(--fg-2); }
.wo__arrow { color: var(--fg-2); }

.detail__body { display: grid; gap: var(--sp-5); }
.detail--empty { padding: var(--sp-8); text-align: center; color: var(--fg-2); }

.kv { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--sp-2); }
.kv > div { display: grid; gap: 2px; padding: var(--sp-2) var(--sp-3); background: var(--bg-2); border-radius: var(--r-md); }
.kv span { font-size: 10px; color: var(--fg-2); }
.kv b { font-size: var(--fs-sm); font-weight: 600; }

.block { display: grid; gap: var(--sp-2); }
.block h3 { font-size: var(--fs-sm); }
.block p { font-size: var(--fs-sm); color: var(--fg-1); line-height: var(--lh-loose); }
.metric-line {
  font-size: var(--fs-sm);
  color: var(--fg-0) !important;
  padding: var(--sp-2) var(--sp-3);
  background: var(--bg-2);
  border-radius: var(--r-md);
  border-left: 3px solid var(--danger);
}

.tl { display: grid; gap: var(--sp-3); position: relative; }
.tl li { display: grid; grid-template-columns: 14px minmax(0, 1fr); gap: var(--sp-3); position: relative; }
.tl li:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 6px; top: 16px; bottom: -12px;
  width: 1px;
  background: var(--line);
}
.tl__dot {
  width: 9px; height: 9px; margin-top: 6px;
  border-radius: 50%; background: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-dim);
}
.tl__card { padding: var(--sp-2) var(--sp-3); background: var(--bg-2); border-radius: var(--r-md); }
.tl__head { display: flex; justify-content: space-between; margin-bottom: 2px; }
.tl__by { display: inline-flex; align-items: center; gap: 4px; font-size: var(--fs-xs); color: var(--fg-1); font-weight: 600; }
.tl__at { font-size: 10px; color: var(--fg-2); }
.tl__card p { font-size: var(--fs-xs) !important; }

.actions__row { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.actions__note { font-size: var(--fs-xs) !important; color: var(--fg-2) !important; }

.btn {
  display: inline-flex; align-items: center; gap: var(--sp-1);
  height: 32px; padding: 0 var(--sp-4);
  border-radius: var(--r-md); font-size: var(--fs-sm);
  transition: background var(--t-fast) var(--ease);
}
.btn--ghost { border: 1px solid var(--line); color: var(--fg-1); }
.btn--ghost:hover { background: var(--bg-2); color: var(--fg-0); }
.btn--primary { background: var(--brand); color: #14171c; font-weight: 600; }
.btn--primary:hover { background: var(--brand-soft); }

@media (max-width: 1200px) {
  .iv__main { grid-template-columns: 1fr; }
  .kv { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
