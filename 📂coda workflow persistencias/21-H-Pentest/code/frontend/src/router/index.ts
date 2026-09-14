import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Monitor from '@/views/Monitor.vue'
import TaskList from '@/views/TaskList.vue'
import Report from '@/views/Report.vue'
import Settings from '@/views/Settings.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard,
      meta: { title: '仪表盘' }
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: TaskList,
      meta: { title: '任务管理' }
    },
    {
      path: '/monitor/:id',
      name: 'monitor',
      component: Monitor,
      meta: { title: '实时监控' }
    },
    {
      path: '/report/:id',
      name: 'report',
      component: Report,
      meta: { title: '测试报告' }
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings,
      meta: { title: '系统配置' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} - H-Pentest` || 'H-Pentest'
  next()
})

export default router
