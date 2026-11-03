<script setup lang="ts">
import { computed, watch, onUnmounted, nextTick, ref } from 'vue'
import { X, MapPin, Clock, Package, Boxes, ArrowRight } from 'lucide-vue-next'
import { SITES, isOpenNow } from '@/data/sites'
import type { Scenario } from '@/data/types'
import { simSeries } from '@/composables/useData'
import StatusDot from './StatusDot.vue'
import StationPlan from './StationPlan.vue'

const props = defineProps<{
  open: boolean
  siteId: string | null
  scenario: Scenario
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'go-sites'): void
}>()

const closeBtn = ref<HTMLButtonElement | null>(null)
let lastFocused: HTMLElement | null = null

/** Esc 关闭 + 打开时把焦点移进抽屉，关闭后焦点回原位（键盘用户不会"丢失光标"） */
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    e.stopPropagation()
    emit('update:open', false)
  }
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      lastFocused = document.activeElement as HTMLElement | null
      document.addEventListener('keydown', onKeydown)
      await nextTick()
      closeBtn.value?.focus()
    } else {
      document.removeEventListener('keydown', onKeydown)
      lastFocused?.focus?.()
      lastFocused = null
    }
  }
)

onUnmounted(() => document.removeEventListener('keydown', onKeydown))

const site = computed(() => SITES.find((s) => s.id === props.siteId) ?? null)
const sum = computed(() => props.scenario.summary.find((s) => s.site_id === props.siteId) ?? null)
const rows = computed(() => (props.siteId ? simSeries(props.scenario, props.siteId) : []))
const openNow = computed(() => (site.value ? isOpenNow(site.value) : false))

/** 迷你条形：把该站 33 桶的积压画成一条高度图 */
const spark = computed(() => {
  const r = rows.value
  if (!r.length) return []
  const max = Math.max(1, ...r.map((x) => x.q))
  return r.map((x) => ({
    h: Math.max(2, Math.round((x.q / max) * 40)),
    risk: x.risk_q || x.risk_i,
    bucket: x.bucket,
    q: x.q
  }))
})
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open && site" class="drawer-root">
        <div class="drawer-mask" @click="emit('update:open', false)" />
        <aside class="drawer" role="dialog" aria-modal="true" :aria-label="`${site.name} 详情`">
          <header class="drawer__head">
            <div class="drawer__title">
              <span class="drawer__badge" :style="{ background: site.color }" />
              <div>
                <h2>{{ site.name }}</h2>
                <p class="drawer__sub">{{ site.roleLabel }} · {{ site.area }}</p>
              </div>
            </div>
            <button ref="closeBtn" class="drawer__close" aria-label="关闭" @click="emit('update:open', false)">
              <X :size="18" />
            </button>
          </header>

          <div class="drawer__body">
            <div class="drawer__status">
              <StatusDot :open="openNow" :risk="(sum?.risk_buckets ?? 0) > 0" />
              <span>{{ openNow ? '营业中' : '已闭站' }}</span>
              <span class="drawer__hours"><Clock :size="12" /> {{ site.hours.open }}—{{ site.hours.close }}</span>
            </div>

            <section class="plan-block">
              <h3 class="plan-block__title">室内平面图</h3>
              <StationPlan :site-id="site.id" />
            </section>

            <dl class="facts">
              <div class="fact">
                <dt><MapPin :size="13" /> 位置</dt>
                <dd>{{ site.locationText }}</dd>
              </div>
              <div class="fact">
                <dt><Package :size="13" /> 服务</dt>
                <dd>
                  <span v-for="s in site.services" :key="s" class="svc">{{ s }}</span>
                </dd>
              </div>
            </dl>

            <div class="mini">
              <div class="mini__head">
                <span>本场景积压走势</span>
                <span class="mini__legend">
                  <i /> 风险时段 <i class="mini__ok" /> 正常
                </span>
              </div>
              <div class="spark" role="img" :aria-label="`${site.shortName} 全天积压走势`">
                <span
                  v-for="(b, i) in spark"
                  :key="i"
                  class="spark__bar"
                  :class="{ 'spark__bar--risk': b.risk }"
                  :style="{ height: b.h + 'px' }"
                  :title="`${b.bucket} 积压 ${b.q} 件`"
                />
              </div>
            </div>

            <div class="metrics">
              <div class="metric">
                <span class="metric__k">到件</span>
                <span class="metric__v num">{{ sum?.daily_arrivals ?? 0 }}</span>
              </div>
              <div class="metric">
                <span class="metric__k">取走</span>
                <span class="metric__v num">{{ sum?.total_pickup ?? 0 }}</span>
              </div>
              <div class="metric">
                <span class="metric__k">峰值积压</span>
                <span class="metric__v num">{{ sum?.peak_q ?? 0 }}</span>
              </div>
              <div class="metric">
                <span class="metric__k">峰值待取</span>
                <span class="metric__v num">{{ sum?.peak_i ?? 0 }}</span>
              </div>
              <div class="metric">
                <span class="metric__k">处理上限</span>
                <span class="metric__v num">{{ scenario.sites.find((s) => s.site_id === site!.id)?.params.capacity_per_bucket ?? 0 }}</span>
              </div>
              <div class="metric">
                <span class="metric__k">积压上限</span>
                <span class="metric__v num">{{ scenario.sites.find((s) => s.site_id === site!.id)?.params.kappa_q ?? 0 }}</span>
              </div>
            </div>

            <div class="drawer__foot">
              <span class="tag tag--sim">模拟</span>
              <span class="drawer__hint">业务数值为演示假设；位置与营业时间来自公开资料</span>
            </div>
          </div>

          <footer class="drawer__actions">
            <button class="btn btn--ghost" @click="emit('update:open', false)">关闭</button>
            <button class="btn btn--primary" @click="emit('go-sites')">
              查看站点详情 <ArrowRight :size="14" />
            </button>
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.plan-block { display: grid; gap: var(--sp-2); margin: var(--sp-3) 0; }
.plan-block__title { font-size: var(--fs-sm); font-weight: 600; color: var(--fg-0); }

.drawer-root { position: fixed; inset: 0; z-index: 60; }
.drawer-mask {
  position: absolute;
  inset: 0;
  background: rgb(0 0 0 / 0.5);
  backdrop-filter: blur(2px);
}

.drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: min(440px, 92vw);
  display: flex;
  flex-direction: column;
  background: var(--bg-1);
  border-left: 1px solid var(--line);
  box-shadow: var(--shadow-3);
}

.drawer__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-5);
  border-bottom: 1px solid var(--line);
}
.drawer__title { display: flex; gap: var(--sp-3); align-items: center; }
.drawer__badge { width: 4px; height: 34px; border-radius: var(--r-pill); }
.drawer__title h2 { font-size: var(--fs-md); }
.drawer__sub { font-size: var(--fs-xs); color: var(--fg-2); margin-top: 2px; }

.drawer__close {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: var(--r-sm);
  color: var(--fg-1);
}
.drawer__close:hover { background: var(--bg-2); color: var(--fg-0); }

.drawer__body { flex: 1 1 auto; overflow-y: auto; padding: var(--sp-5); display: grid; gap: var(--sp-5); }

.drawer__status {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--fs-sm);
  padding: var(--sp-2) var(--sp-3);
  background: var(--bg-2);
  border-radius: var(--r-md);
}
.drawer__hours { margin-left: auto; display: inline-flex; align-items: center; gap: 4px; color: var(--fg-2); font-size: var(--fs-xs); }

.facts { display: grid; gap: var(--sp-3); }
.fact { display: grid; gap: 4px; }
.fact dt { display: flex; align-items: center; gap: 4px; font-size: var(--fs-xs); color: var(--fg-2); }
.fact dd { margin: 0; font-size: var(--fs-sm); line-height: var(--lh-loose); }
.svc {
  display: inline-block;
  margin: 0 var(--sp-1) var(--sp-1) 0;
  padding: 1px var(--sp-2);
  font-size: var(--fs-xs);
  border-radius: var(--r-sm);
  background: var(--bg-2);
  color: var(--fg-1);
}

.mini { display: grid; gap: var(--sp-2); }
.mini__head {
  display: flex; justify-content: space-between; align-items: center;
  font-size: var(--fs-xs); color: var(--fg-2);
}
.mini__legend { display: inline-flex; align-items: center; gap: 4px; }
.mini__legend i { width: 8px; height: 8px; border-radius: 2px; background: var(--danger); display: inline-block; }
.mini__legend i.mini__ok { background: var(--ok); margin-left: var(--sp-2); }

.spark {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 48px;
  padding: var(--sp-1);
  background: var(--bg-2);
  border-radius: var(--r-md);
}
.spark__bar {
  flex: 1 1 0;
  min-width: 2px;
  border-radius: 1px;
  background: var(--ok);
  opacity: 0.75;
}
.spark__bar--risk { background: var(--danger); opacity: 1; }

.metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--sp-2);
}
.metric {
  display: grid; gap: 2px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--bg-2);
  border-radius: var(--r-md);
}
.metric__k { font-size: 10px; color: var(--fg-2); }
.metric__v { font-size: var(--fs-md); font-weight: 600; }

.drawer__foot { display: flex; align-items: center; gap: var(--sp-2); }
.drawer__hint { font-size: var(--fs-xs); color: var(--fg-2); }

.drawer__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-5);
  border-top: 1px solid var(--line);
}

.btn {
  display: inline-flex; align-items: center; gap: var(--sp-1);
  height: 34px; padding: 0 var(--sp-4);
  border-radius: var(--r-md);
  font-size: var(--fs-sm);
  transition: background var(--t-fast) var(--ease);
}
.btn--ghost { border: 1px solid var(--line); color: var(--fg-1); }
.btn--ghost:hover { background: var(--bg-2); color: var(--fg-0); }
.btn--primary { background: var(--brand); color: #14171c; font-weight: 600; }
.btn--primary:hover { background: var(--brand-soft); }

.drawer-enter-active, .drawer-leave-active { transition: opacity var(--t-base) var(--ease); }
.drawer-enter-active .drawer, .drawer-leave-active .drawer { transition: transform var(--t-base) var(--ease); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: translateX(100%); }
</style>
