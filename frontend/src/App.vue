<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import {
  LayoutDashboard, MapPin, TrendingUp, Siren, BookOpen, Sun, Moon, Database, Radio, Crosshair
} from 'lucide-vue-next'
import SiteFooter from '@/components/SiteFooter.vue'
import CalibratePanel from '@/components/CalibratePanel.vue'

const store = useAppStore()
const route = useRoute()

const nav = [
  { to: '/overview', label: '运营总览', code: 'P1', icon: LayoutDashboard },
  { to: '/sites', label: '站点与服务', code: 'P2', icon: MapPin },
  { to: '/peak', label: '高峰与方案', code: 'P3', icon: TrendingUp },
  { to: '/incidents', label: '异常协同', code: 'P4', icon: Siren },
  { to: '/about', label: '资料与说明', code: 'P5', icon: BookOpen }
]

const currentTitle = computed(() => (route.meta.title as string) ?? '')

onMounted(() => store.setTheme(store.theme))

const calOpen = ref(false)
</script>

<template>
  <div class="shell">
    <a class="skip" href="#main">跳到主内容</a>

    <header class="topbar">
      <div class="topbar__brand">
        <span class="topbar__logo" aria-hidden="true">驿</span>
        <span class="topbar__name">
          <strong>驿链</strong>
          <em>CampusFlow</em>
        </span>
        <span class="topbar__sub">中国矿业大学 · 南湖校区</span>
      </div>

      <nav class="topbar__nav" aria-label="主导航">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          active-class="nav-item--on"
        >
          <component :is="item.icon" :size="16" aria-hidden="true" />
          <span>{{ item.label }}</span>
          <span class="nav-item__code">{{ item.code }}</span>
        </RouterLink>
      </nav>

      <div class="topbar__side">
        <span
          v-if="store.isDemoData"
          class="badge badge--demo"
          title="未连接后端接口（/api/scenarios 不可达），当前使用内置演示样例数据"
        >
          <Database :size="13" aria-hidden="true" />
          演示数据模式
        </span>
        <span v-else class="badge badge--live" title="数据来自后端 /api/scenarios 接口">
          <Radio :size="13" aria-hidden="true" />
          接口数据
        </span>
        <button
          class="icon-btn icon-btn--theme"
          :aria-label="store.theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'"
          @click="store.toggleTheme()"
        >
          <Sun v-if="store.theme === 'dark'" :size="16" />
          <Moon v-else :size="16" />
        </button>
        <button class="icon-btn" aria-label="校准站点位置" title="校准站点位置" @click="calOpen = true">
          <Crosshair :size="16" />
        </button>
      </div>
    </header>

    <main id="main" class="main">
      <div class="main__head">
        <h1>{{ currentTitle }}</h1>
        <p class="main__note">课程演示原型 · 数据分为「公开资料 / 演示假设 / 待核实」三类，页面内分别标注</p>
      </div>
      <RouterView />
    </main>

    <SiteFooter />

    <CalibratePanel v-model:open="calOpen" />
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.skip {
  position: fixed;
  top: var(--sp-3);
  left: var(--sp-3);
  z-index: 99;
  padding: var(--sp-2) var(--sp-4);
  background: var(--bg-2);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-md);
  clip-path: inset(50%);
  white-space: nowrap;
}
.skip:focus {
  clip-path: none;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: var(--sp-6);
  height: var(--nav-h);
  padding: 0 var(--sp-5);
  background: color-mix(in srgb, var(--bg-0) 88%, transparent);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--line);
}

.topbar__brand {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex: 0 0 auto;
}

.topbar__logo {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: var(--r-md);
  background: var(--fg-0);
  color: var(--bg-0);
  font-weight: 700;
  font-size: var(--fs-md);
}

.topbar__name {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
}
.topbar__name strong { font-size: var(--fs-md); }
.topbar__name em {
  font-style: normal;
  font-size: var(--fs-xs);
  color: var(--fg-2);
  letter-spacing: 0.06em;
}

.topbar__sub {
  font-size: var(--fs-xs);
  color: var(--fg-2);
  padding-left: var(--sp-3);
  border-left: 1px solid var(--line);
  white-space: nowrap;
}

.topbar__nav {
  display: flex;
  gap: var(--sp-1);
  flex: 1 1 auto;
  overflow-x: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  height: 34px;
  padding: 0 var(--sp-3);
  border-radius: var(--r-md);
  color: var(--fg-1);
  font-size: var(--fs-base);
  white-space: nowrap;
  transition: background var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
}
.nav-item:hover { background: var(--bg-2); color: var(--fg-0); }
.nav-item--on {
  background: var(--bg-3);
  color: var(--fg-0);
  font-weight: 600;
}

.nav-item__code {
  font-size: 10px;
  color: var(--fg-2);
  letter-spacing: 0.04em;
}

.topbar__side {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex: 0 0 auto;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: 3px var(--sp-2);
  border-radius: var(--r-pill);
  font-size: var(--fs-xs);
  border: 1px solid var(--line-strong);
  color: var(--fg-1);
  white-space: nowrap;
}
.badge--demo {
  border-style: dashed;
  color: var(--warn-ink);
  border-color: color-mix(in srgb, var(--warn) 40%, var(--line-strong));
}
.badge--live {
  color: var(--ok-ink);
  border-color: color-mix(in srgb, var(--ok) 40%, var(--line-strong));
}

.icon-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  color: var(--fg-1);
  transition: background var(--t-fast) var(--ease);
}
.icon-btn:hover { background: var(--bg-2); color: var(--fg-0); }

.main {
  flex: 1 1 auto;
  width: 100%;
  max-width: var(--max-w);
  margin: 0 auto;
  padding: var(--sp-6) var(--sp-5) var(--sp-8);
}

.main__head {
  display: flex;
  align-items: baseline;
  gap: var(--sp-4);
  flex-wrap: wrap;
  margin-bottom: var(--sp-5);
}
.main__head h1 { font-size: var(--fs-xl); }
.main__note {
  font-size: var(--fs-xs);
  color: var(--fg-2);
}

@media (max-width: 1100px) {
  .topbar__sub { display: none; }
}
</style>
