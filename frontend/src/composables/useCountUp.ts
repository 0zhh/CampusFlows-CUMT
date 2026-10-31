import { ref, watch, onUnmounted, type Ref } from 'vue'

/** 数字滚动：场景切换时让 KPI 平滑过渡，避免瞬时跳变 */
export function useCountUp(source: Ref<number>, duration = 600) {
  const display = ref(source.value)
  let raf = 0

  function run(from: number, to: number) {
    cancelAnimationFrame(raf)
    const t0 = performance.now()
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / duration)
      const eased = 1 - Math.pow(1 - k, 3)
      display.value = Math.round(from + (to - from) * eased)
      if (k < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
  }

  watch(source, (to, from) => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      display.value = to
      return
    }
    run(from ?? 0, to)
  })

  onUnmounted(() => cancelAnimationFrame(raf))

  return display
}
