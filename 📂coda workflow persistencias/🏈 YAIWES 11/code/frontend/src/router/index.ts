import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/pages/index.vue'),
    },
    {
      path: '/session/new',
      name: 'new-session',
      component: () => import('@/pages/session/new.vue'),
    },
    {
      path: '/session/:taskId',
      name: 'solve-screen',
      component: () => import('@/pages/session/[id].vue'),
      props: true,
    },
    {
      path: '/kb',
      name: 'knowledge-base',
      component: () => import('@/pages/kb/index.vue'),
    },
    {
      path: '/status',
      name: 'status',
      component: () => import('@/pages/status/index.vue'),
    },
  ],
})

export default router
