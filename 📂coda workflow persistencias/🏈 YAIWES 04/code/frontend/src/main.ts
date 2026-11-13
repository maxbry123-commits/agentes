import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import TDesign from 'tdesign-vue-next'
import 'tdesign-vue-next/es/style/index.css'
import './style.css'
import App from './App.vue'

// 路由配置
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('./views/Dashboard.vue'),
    },
    {
      path: '/targets',
      name: 'Targets',
      component: () => import('./views/Targets.vue'),
    },
    {
      path: '/scan',
      name: 'Scan',
      component: () => import('./views/Scan.vue'),
    },
    {
      path: '/vulnerabilities',
      name: 'Vulnerabilities',
      component: () => import('./views/Vulnerabilities.vue'),
    },
    {
      path: '/reports',
      name: 'Reports',
      component: () => import('./views/Reports.vue'),
    },
    {
      path: '/agents',
      name: 'Agents',
      component: () => import('./views/Agents.vue'),
    },
    {
      path: '/sessions',
      name: 'Sessions',
      component: () => import('./views/SessionDetail.vue'),
    },
    {
      path: '/sessions/:sessionId',
      name: 'SessionDetail',
      component: () => import('./views/SessionDetail.vue'),
    },
    {
      path: '/tools',
      name: 'Tools',
      component: () => import('./views/Tools.vue'),
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('./views/Settings.vue'),
    },
    {
      path: '/attack-chain',
      name: 'AttackChain',
      component: () => import('./views/AttackChain.vue'),
    },
  ],
})

const app = createApp(App)

app.use(TDesign)
app.use(router)

app.mount('#app')
