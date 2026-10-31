<script setup lang="ts">
import { computed, toRef, type Component } from 'vue'
import { useCountUp } from '@/composables/useCountUp'

const props = defineProps<{
  label: string
  value: number
  unit?: string
  hint?: string
  tone?: 'default' | 'ok' | 'warn' | 'danger'
  icon?: Component
  /** 是否为演示假设数据 */
  simulated?: boolean
}>()

const display = useCountUp(toRef(props, 'value'))
const toneClass = computed(() => `kpi--${props.tone ?? 'default'}`)
</script>

<template>
  <div class="kpi" :class="toneClass">
    <div class="kpi__top">
      <span v-if="icon" class="kpi__icon"><component :is="icon" :size="15" /></span>
      <span class="kpi__label">{{ label }}</span>
      <span v-if="simulated" class="tag tag--sim">模拟</span>
    </div>
    <div class="kpi__value">
      <span class="num">{{ display.toLocaleString('zh-CN') }}</span>
      <span v-if="unit" class="kpi__unit">{{ unit }}</span>
    </div>
    <p v-if="hint" class="kpi__hint">{{ hint }}</p>
  </div>
</template>

<style scoped>
.kpi {
  position: relative;
  display: grid;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-5);
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-1);
  overflow: hidden;
}

.kpi::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--line-strong);
}
.kpi--ok::after { background: var(--ok); }
.kpi--warn::after { background: var(--warn); }
.kpi--danger::after { background: var(--danger); }

.kpi__top {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--fs-xs);
  color: var(--fg-1);
}
.kpi__icon { color: var(--fg-2); display: inline-flex; }
.kpi__label { flex: 1 1 auto; }

.kpi__value {
  display: flex;
  align-items: baseline;
  gap: var(--sp-1);
  font-size: var(--fs-2xl);
  font-weight: 600;
  line-height: 1.1;
}
.kpi__unit { font-size: var(--fs-sm); color: var(--fg-2); font-weight: 400; }

.kpi__hint { font-size: var(--fs-xs); color: var(--fg-2); }
</style>
