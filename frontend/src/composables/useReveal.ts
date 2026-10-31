/**
 * 页面进场动效。只动 opacity 和 translateY，不动会影响布局的属性，
 * 所以动画过程中不会引起任何重排或溢出。
 * 系统开了"减少动态效果"就整体跳过。
 */
import { onMounted, onUnmounted } from 'vue'
import gsap from 'gsap'

export function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function useReveal(selector = '.panel, .kpis > *', opts: { y?: number; stagger?: number } = {}) {
  let ctx: gsap.Context | null = null

  onMounted(() => {
    if (prefersReducedMotion()) return
    const targets = Array.from(document.querySelectorAll(selector))
    if (!targets.length) return
    ctx = gsap.context(() => {
      gsap.from(targets, {
        opacity: 0,
        y: opts.y ?? 12,
        duration: 0.42,
        stagger: opts.stagger ?? 0.045,
        ease: 'power2.out',
        clearProps: 'opacity,transform'
      })
    })
  })

  onUnmounted(() => {
    ctx?.revert()
    ctx = null
  })
}
