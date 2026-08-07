<template>
  <el-container class="layout">
    <!-- 侧边栏：6 大模块 -->
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <span v-if="!collapsed" class="logo-text">智慧农业管理系统</span>
        <span v-else class="logo-mini">农</span>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="collapsed"
        :collapse-transition="false"
        background-color="transparent"
        text-color="#a6b8d0"
        active-text-color="#4f9dff"
        @select="onMenuSelect"
      >
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
      <div class="collapse-btn" @click="collapsed = !collapsed">
        <el-icon><component :is="collapsed ? 'Expand' : 'Fold'" /></el-icon>
      </div>
    </el-aside>

    <el-container>
      <!-- 顶栏：面包屑 / 主题切换 / 用户 / 退出 -->
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tooltip :content="theme.dark ? '切换浅色主题' : '切换深色主题'">
            <el-button circle :icon="theme.dark ? 'Sunny' : 'Moon'" @click="theme.toggle()" />
          </el-tooltip>
          <el-dropdown @command="onCommand">
            <span class="user-box">
              <el-icon><UserFilled /></el-icon>
              <span class="user-name">{{ auth.username || '管理员' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useThemeStore } from '../stores/theme'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const theme = useThemeStore()
const auth = useAuthStore()
const collapsed = ref(false)

const menus = [
  { path: '/cockpit', title: '驾驶舱', icon: 'Odometer' },
  { path: '/screen', title: '数字孪生大屏', icon: 'DataBoard' },
  { path: '/data', title: '数据管理', icon: 'Grid' },
  { path: '/devices', title: '设备中心', icon: 'Monitor' },
  { path: '/gis', title: '农田GIS', icon: 'MapLocation' },
  { path: '/env', title: '环境监测', icon: 'DataLine' },
  { path: '/analytics', title: '分析报表', icon: 'TrendCharts' },
]

// 菜单统一站内路由跳转（含 /screen 数字孪生大屏，由路由页内嵌 iframe）
function onMenuSelect(index) {
  router.push(index)
}

const currentTitle = computed(() => route.meta.title || '驾驶舱')

async function onCommand(cmd) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
    auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout { height: 100vh; }
.sidebar {
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
  border-right: 1px solid var(--border-color);
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #1d6fe0, #4f9dff);
}
.logo-text { font-size: 15px; white-space: nowrap; }
.logo-mini { font-size: 18px; }
.sidebar :deep(.el-menu) { border-right: none; }
.collapse-btn {
  margin-top: auto;
  padding: 12px 0;
  text-align: center;
  color: #a6b8d0;
  cursor: pointer;
  font-size: 18px;
}
.collapse-btn:hover { color: #fff; }
.header {
  background: var(--bg-header);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.header-right { display: flex; align-items: center; gap: 12px; }
.user-box {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--text-main);
}
.main {
  background: var(--bg-page);
  padding: 0;
  overflow-y: auto;
}
</style>