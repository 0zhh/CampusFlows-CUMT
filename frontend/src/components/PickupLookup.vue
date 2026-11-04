<script setup lang="ts">
/**
 * 取件码查询：输入 108-3-2441，返回货架/层/位/承运商。
 * 数据来自 MySQL 形态的 /api/pickup/{code}（五表连接）；后端不可达时给出明确提示。
 */
import { ref } from 'vue'
import { Search, MapPin } from 'lucide-vue-next'
import { getPickup, type PickupInfo } from '@/data/mysql'

const code = ref('')
const result = ref<PickupInfo | null>(null)
const state = ref<'idle' | 'loading' | 'ok' | 'miss' | 'offline'>('idle')

async function search() {
  const c = code.value.trim()
  if (!c) return
  state.value = 'loading'
  result.value = null
  const r = await getPickup(c)
  if (r) {
    result.value = r
    state.value = 'ok'
  } else {
    // 区分"没有这个码"和"后端没起"：再打一次健康检查
    const alive = await fetch('/api/health').then((x) => x.ok).catch(() => false)
    state.value = alive ? 'miss' : 'offline'
  }
}

function sample() {
  code.value = '1-1-1000'
  void search()
}
</script>

<template>
  <div class="pk">
    <div class="pk__row">
      <input
        v-model="code"
        class="pk__input"
        placeholder="输入取件码，如 108-3-2441"
        aria-label="取件码"
        @keyup.enter="search"
      />
      <button class="btn btn--primary" :disabled="state === 'loading'" @click="search">
        <Search :size="14" /> 查询
      </button>
    </div>

    <p v-if="state === 'idle'" class="pk__hint">
      取件码规则：<code>货架号-层号-四位序号</code>。
      <button class="pk__link" @click="sample">试一个样例</button>
    </p>

    <p v-else-if="state === 'loading'" class="pk__hint">查询中…</p>
    <p v-else-if="state === 'miss'" class="pk__hint pk__hint--warn">没有这个取件码。</p>
    <p v-else-if="state === 'offline'" class="pk__hint pk__hint--warn">
      取件码查询需要后端（MySQL 形态），当前未连接。
    </p>

    <div v-else-if="result" class="pk__card">
      <div class="pk__code num">{{ result.code }}</div>
      <ul class="pk__facts">
        <li><span>站点</span><b>{{ result.siteName ?? result.siteId }}</b></li>
        <li><span>位置</span><b><MapPin :size="12" /> {{ result.zoneId }} · {{ result.shelfNo }} 号架 {{ result.tier }} 层第 {{ result.cell }} 位</b></li>
        <li><span>承运商</span><b>{{ result.carrier }}</b></li>
        <li><span>入架</span><b class="num">{{ String(result.shelvedAt).replace('T', ' ').slice(0, 16) }}</b></li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.pk { display: grid; gap: var(--sp-2); }
.pk__row { display: flex; gap: var(--sp-2); }
.pk__input {
  flex: 1 1 auto;
  min-width: 0;
  padding: 6px var(--sp-3);
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  color: var(--fg-0);
  font-size: var(--fs-sm);
}
.pk__input:focus { outline: 2px solid var(--brand); outline-offset: 1px; }
.pk__hint { font-size: var(--fs-xs); color: var(--fg-2); }
.pk__hint--warn { color: var(--warn-ink); }
.pk__link { color: var(--info-ink); text-decoration: underline; font-size: var(--fs-xs); }
.pk__card {
  display: grid;
  gap: var(--sp-2);
  padding: var(--sp-3);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--bg-2);
}
.pk__code { font-size: var(--fs-lg); font-weight: 600; color: var(--brand); }
.pk__facts { display: grid; gap: 4px; font-size: var(--fs-xs); }
.pk__facts li { display: flex; gap: var(--sp-2); }
.pk__facts span { color: var(--fg-2); min-width: 52px; }
.pk__facts b { color: var(--fg-0); font-weight: 500; display: inline-flex; align-items: center; gap: 4px; }
</style>
