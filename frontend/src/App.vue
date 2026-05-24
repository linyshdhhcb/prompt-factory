<template>
  <el-container class="app-container">
    <el-aside width="220px" class="app-aside">
      <div class="app-logo">
        <h2>Prompt 工厂基座</h2>
      </div>
      <el-menu
        :default-active="currentRoute"
        router
        class="app-menu"
        background-color="transparent"
        text-color="#94A3B8"
        active-text-color="#38BDF8"
      >
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <span>项目管理</span>
        </el-menu-item>
        <el-menu-item index="/personas">
          <el-icon><User /></el-icon>
          <span>人格管理</span>
        </el-menu-item>
        <el-menu-item index="/templates">
          <el-icon><Document /></el-icon>
          <span>模板管理</span>
        </el-menu-item>
        <el-menu-item index="/postprocess">
          <el-icon><SetUp /></el-icon>
          <span>后处理规则</span>
        </el-menu-item>
        <el-menu-item index="/models">
          <el-icon><Monitor /></el-icon>
          <span>模型管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <span class="header-title">Prompt 工厂基座</span>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataBoard, Folder, User, Document, SetUp, Monitor } from '@element-plus/icons-vue'

const route = useRoute()
const currentRoute = computed(() => {
  const path = route.path
  if (path.startsWith('/projects')) return '/projects'
  if (path.startsWith('/personas')) return '/personas'
  if (path.startsWith('/templates')) return '/templates'
  if (path.startsWith('/postprocess')) return '/postprocess'
  if (path.startsWith('/models')) return '/models'
  return path
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&display=swap');

html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
  background: #020617;
  color: #F8FAFC;
}

html.dark {
  color-scheme: dark;
}

.el-main {
  background: transparent !important;
  color: #F8FAFC !important;
}

.el-aside {
  background: transparent !important;
}

.el-header {
  background: transparent !important;
  color: #F8FAFC !important;
}

.el-container {
  background: transparent !important;
}

.app-container {
  height: 100vh;
}

.app-aside {
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  overflow-y: auto;
}

.app-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #F8FAFC;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
  overflow: hidden;
}

.app-logo::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
}

.app-logo h2 {
  margin: 0;
  font-size: 16px;
  white-space: nowrap;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.app-menu {
  border-right: none;
  background-color: transparent !important;
}

.app-menu .el-menu-item {
  background-color: transparent !important;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.app-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.06) !important;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #F8FAFC !important;
}

.app-menu .el-menu-item:hover::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), transparent);
  pointer-events: none;
}

.app-menu .el-menu-item.is-active {
  color: #38BDF8 !important;
  background: rgba(56, 189, 248, 0.1) !important;
  border-right: 2px solid #38BDF8;
}

.app-header {
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.3);
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #F8FAFC;
  letter-spacing: 0.3px;
}

.app-main {
  background: linear-gradient(135deg, #020617 0%, #0F172A 50%, #1E293B 100%);
  min-height: 0;
  overflow-y: auto;
}
</style>
