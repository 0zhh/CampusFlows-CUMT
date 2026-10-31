<script setup lang="ts">
defineProps<{ open: boolean; risk?: boolean }>()
</script>

<template>
  <span class="dot" :class="[open ? 'dot--on' : 'dot--off', { 'dot--risk': risk }]">
    <span class="dot__core" />
  </span>
</template>

<style scoped>
.dot {
  position: relative;
  display: inline-grid;
  place-items: center;
  width: 14px;
  height: 14px;
  flex: 0 0 auto;
}
.dot__core {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--fg-2);
}
.dot--on .dot__core { background: var(--ok); box-shadow: 0 0 0 3px var(--ok-dim); }
.dot--off .dot__core { background: var(--fg-2); }

.dot::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid transparent;
}
.dot--on::before { border-color: rgb(62 201 167 / 0.35); }

.dot--risk .dot__core { background: var(--danger); box-shadow: 0 0 0 3px var(--danger-dim); }
.dot--risk::before {
  border-color: var(--danger);
  animation: ping 1.6s ease-out infinite;
}
@keyframes ping {
  0% { transform: scale(0.8); opacity: 0.9; }
  100% { transform: scale(1.7); opacity: 0; }
}
</style>
