<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { useScenarios } from '@/composables/useData'

const store = useAppStore()
const scenarios = useScenarios()
const current = computed(() => scenarios.find((s) => s.scenario_id === store.scenarioId) ?? scenarios[0])
</script>

<template>
  <div class="picker">
    <div class="picker__tabs" role="tablist" aria-label="演示场景切换">
      <button
        v-for="s in scenarios"
        :key="s.scenario_id"
        class="picker__tab"
        :class="{ 'picker__tab--on': store.scenarioId === s.scenario_id }"
        role="tab"
        :aria-selected="store.scenarioId === s.scenario_id"
        @click="store.scenarioId = s.scenario_id"
      >
        <span class="picker__name">{{ s.name }}</span>
        <span class="picker__id">{{ s.scenario_id }}</span>
      </button>
    </div>
    <p class="picker__note">
      <span class="tag tag--sim">模拟</span>
      {{ current.note }}
    </p>
  </div>
</template>

<style scoped>
.picker { display: grid; gap: var(--sp-2); }

.picker__tabs {
  display: inline-flex;
  gap: var(--sp-1);
  padding: var(--sp-1);
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  width: fit-content;
  max-width: 100%;
  overflow-x: auto;
}

.picker__tab {
  display: grid;
  gap: 1px;
  padding: var(--sp-2) var(--sp-4);
  border-radius: var(--r-sm);
  text-align: left;
  color: var(--fg-1);
  white-space: nowrap;
  transition: background var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
}
.picker__tab:hover { background: var(--bg-3); color: var(--fg-0); }
.picker__tab--on {
  background: var(--brand-dim);
  color: var(--brand);
  box-shadow: inset 0 0 0 1px rgb(232 163 61 / 0.35);
}
.picker__name { font-size: var(--fs-sm); font-weight: 600; }
.picker__id { font-size: 10px; color: var(--fg-2); letter-spacing: 0.04em; }
.picker__tab--on .picker__id { color: rgb(232 163 61 / 0.7); }

.picker__note {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--fs-xs);
  color: var(--fg-2);
}
</style>
