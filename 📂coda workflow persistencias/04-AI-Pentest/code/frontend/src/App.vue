<template>
  <div class="min-h-screen bg-slate-900">
    <div class="relative z-10 flex min-h-screen">
      <aside class="w-64 bg-slate-900 border-r border-slate-700 flex flex-col">
        <div class="h-16 flex items-center px-6 border-b border-slate-700 bg-slate-800/80">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-lg bg-slate-700 flex items-center justify-center">
              <Shield class="w-5 h-5 text-white" />
            </div>
            <div>
              <span class="text-lg font-bold text-white">AI-Pentest</span>
              <p class="text-[10px] text-slate-400 -mt-1">渗透测试系统</p>
            </div>
          </div>
        </div>
        <nav class="flex-1 py-4 px-3">
          <t-menu :value="activeMenu" @change="handleMenuChange" theme="dark">
            <t-menu-item value="settings">
              <template #icon><Settings class="w-5 h-5" /></template>
              系统设置
            </t-menu-item>
            <t-menu-divider />
            <t-menu-item value="dashboard">
              <template #icon><LayoutDashboard class="w-5 h-5" /></template>
              控制台
            </t-menu-item>
            <t-menu-item value="targets">
              <template #icon><Target class="w-5 h-5" /></template>
              目标管理
            </t-menu-item>
            <t-menu-item value="scan">
              <template #icon><Radar class="w-5 h-5" /></template>
              扫描任务
            </t-menu-item>
            <t-menu-item value="vulnerabilities">
              <template #icon><Bug class="w-5 h-5" /></template>
              漏洞管理
            </t-menu-item>
            <t-menu-item value="reports">
              <template #icon><FileText class="w-5 h-5" /></template>
              测试报告
            </t-menu-item>
            <t-menu-item value="agents">
              <template #icon><Bot class="w-5 h-5" /></template>
              智能体
            </t-menu-item>
            <t-menu-item value="sessions">
              <template #icon><MessagesSquare class="w-5 h-5" /></template>
              会话观测
            </t-menu-item>
            <t-menu-item value="attack-chain">
              <template #icon><Route class="w-5 h-5" /></template>
              攻击链路
            </t-menu-item>
            <t-menu-item value="tools">
              <template #icon><Wrench class="w-5 h-5" /></template>
              工具集成
            </t-menu-item>
          </t-menu>
        </nav>
        <div class="p-4 border-t border-slate-700">
          <div class="flex items-center gap-2 text-xs text-slate-400">
            <div class="w-2 h-2 rounded-full bg-green-500"></div>
            <span>系统正常运行</span>
          </div>
        </div>
      </aside>
      <div class="flex-1 flex flex-col">
        <header class="h-16 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-6">
          <h1 class="text-xl font-semibold text-white">{{ pageTitle }}</h1>
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
              <span class="status-dot status-running"></span>
              <span class="text-sm text-slate-300">运行中</span>
            </div>
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
              <Cpu class="w-4 h-4 text-cyan-400" />
              <span class="text-sm text-slate-300">DeepSeek</span>
            </div>
          </div>
        </header>
        <main class="flex-1 overflow-auto p-6">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Shield, LayoutDashboard, Target, Radar, Bug, FileText, Wrench, Settings, Cpu, Bot, Route, MessagesSquare } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const activeMenu = ref('dashboard')

const menuRouteMap: Record<string, string> = {
  dashboard: '/',
  targets: '/targets',
  scan: '/scan',
  vulnerabilities: '/vulnerabilities',
  reports: '/reports',
  agents: '/agents',
  sessions: '/sessions',
  'attack-chain': '/attack-chain',
  tools: '/tools',
  settings: '/settings',
}

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    dashboard: '控制台',
    targets: '目标管理',
    scan: '扫描任务',
    vulnerabilities: '漏洞管理',
    reports: '测试报告',
    agents: '智能体',
    sessions: '会话观测',
    'attack-chain': '攻击链路',
    tools: '工具集成',
    settings: '系统设置',
  }
  return titles[activeMenu.value] || '控制台'
})

const handleMenuChange = (value: string) => {
  activeMenu.value = value
  const route = menuRouteMap[value]
  if (route) router.push(route)
}

const syncActiveMenu = (path: string) => {
  if (path.startsWith('/sessions')) {
    activeMenu.value = 'sessions'
    return
  }

  for (const [key, value] of Object.entries(menuRouteMap)) {
    if (value === path) {
      activeMenu.value = key
      return
    }
  }
}

onMounted(() => {
  syncActiveMenu(window.location.pathname)
})

watch(
  () => route.path,
  (path) => {
    syncActiveMenu(path)
  }
)
</script>

<style>
.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.status-running { background: #10b981; }
.t-menu--dark { background: transparent !important; }
.t-menu__item { border-radius: 8px !important; margin: 2px 0 !important; }
.t-menu__item:hover { background: rgba(59, 130, 246, 0.15) !important; }
.t-menu__item.t-is-active { background: rgba(59, 130, 246, 0.18) !important; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: rgba(30, 41, 59, 0.5); }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #475569, #334155); border-radius: 4px; }
</style>
