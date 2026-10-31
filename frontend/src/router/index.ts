import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/overview' },
  {
    path: '/overview',
    name: 'overview',
    component: () => import('@/views/OverviewView.vue'),
    meta: { title: '运营总览', code: 'P1', icon: 'LayoutDashboard' }
  },
  {
    path: '/sites',
    name: 'sites',
    component: () => import('@/views/SitesView.vue'),
    meta: { title: '站点与服务', code: 'P2', icon: 'MapPin' }
  },
  {
    path: '/peak',
    name: 'peak',
    component: () => import('@/views/PeakView.vue'),
    meta: { title: '高峰与方案', code: 'P3', icon: 'TrendingUp' }
  },
  {
    path: '/incidents',
    name: 'incidents',
    component: () => import('@/views/IncidentsView.vue'),
    meta: { title: '异常协同', code: 'P4', icon: 'Siren' }
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('@/views/AboutView.vue'),
    meta: { title: '资料与说明', code: 'P5', icon: 'BookOpen' }
  },
  { path: '/:pathMatch(.*)*', redirect: '/overview' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.afterEach((to) => {
  const t = (to.meta.title as string) || '驿链'
  document.title = `${t} · 驿链 CampusFlow`
})

export default router
