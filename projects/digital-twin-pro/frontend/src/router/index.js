import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/cockpit',
    children: [
      { path: 'cockpit', name: 'cockpit', component: () => import('../views/cockpit/index.vue'), meta: { title: '驾驶舱', icon: 'Odometer' } },
      { path: 'screen', name: 'screen', component: () => import('../views/screen/index.vue'), meta: { title: '数字孪生大屏', icon: 'DataBoard' } },
      { path: 'data', name: 'data', component: () => import('../views/data/index.vue'), meta: { title: '数据管理', icon: 'Grid' } },
      { path: 'devices', name: 'devices', component: () => import('../views/devices/index.vue'), meta: { title: '设备中心', icon: 'Monitor' } },
      { path: 'gis', name: 'gis', component: () => import('../views/gis/index.vue'), meta: { title: '农田GIS', icon: 'MapLocation' } },
      { path: 'env', name: 'env', component: () => import('../views/env/index.vue'), meta: { title: '环境监测', icon: 'DataLine' } },
      { path: 'analytics', name: 'analytics', component: () => import('../views/analytics/index.vue'), meta: { title: '分析报表', icon: 'TrendCharts' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/cockpit' },
]

const router = createRouter({ history: createWebHistory(), routes })

// 登录守卫：无 token 一律跳 /login
router.beforeEach((to) => {
  const token = localStorage.getItem('agri_admin_token')
  if (!to.meta.public && !token) {
    return { path: '/login', query: to.fullPath !== '/login' ? { redirect: to.fullPath } : {} }
  }
  if (to.path === '/login' && token) return '/cockpit'
  return true
})

export default router