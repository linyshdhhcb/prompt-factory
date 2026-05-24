<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <div class="glass-card stat-card stat-blue">
          <div class="glass-shine"></div>
          <div class="stat-icon-wrap stat-icon-blue">
            <el-icon :size="28"><Folder /></el-icon>
          </div>
          <div class="stat-value">{{ projectCount }}</div>
          <div class="stat-title">项目数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="glass-card stat-card stat-green">
          <div class="glass-shine"></div>
          <div class="stat-icon-wrap stat-icon-green">
            <el-icon :size="28"><Promotion /></el-icon>
          </div>
          <div class="stat-value">{{ todayCount }}</div>
          <div class="stat-title">今日生成量</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="glass-card stat-card stat-orange">
          <div class="glass-shine"></div>
          <div class="stat-icon-wrap stat-icon-orange">
            <el-icon :size="28"><Monitor /></el-icon>
          </div>
          <div class="stat-value">{{ modelStatus }}</div>
          <div class="stat-title">模型状态</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="glass-card stat-card stat-purple">
          <div class="glass-shine"></div>
          <div class="stat-icon-wrap stat-icon-purple">
            <el-icon :size="28"><Document /></el-icon>
          </div>
          <div class="stat-value">{{ recentCount }}</div>
          <div class="stat-title">最近生成记录</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="action-row">
      <el-col :span="24">
        <div class="glass-card">
          <div class="glass-shine"></div>
          <div class="card-header">
            <span class="card-header-text">快捷操作</span>
          </div>
          <div class="card-body">
            <button class="glass-btn glass-btn-primary" @click="$router.push('/projects')">
              <el-icon><Plus /></el-icon>
              新建项目
            </button>
            <button class="glass-btn glass-btn-cta" @click="$router.push('/projects')">
              <el-icon><Promotion /></el-icon>
              开始生成
            </button>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="info-row">
      <el-col :span="12">
        <div class="glass-card">
          <div class="glass-shine"></div>
          <div class="card-header">
            <span class="card-header-text">系统健康</span>
          </div>
          <div class="card-body">
            <el-descriptions :column="1" border v-if="healthInfo" class="dark-descriptions">
              <el-descriptions-item label="状态">
                <el-tag :type="healthInfo.status === 'ok' ? 'success' : 'danger'">
                  {{ healthInfo.status }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="版本">{{ healthInfo.version }}</el-descriptions-item>
              <el-descriptions-item label="运行时间">{{ formatUptime(healthInfo.uptime_seconds) }}</el-descriptions-item>
            </el-descriptions>
            <el-skeleton v-else :rows="3" animated />
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="glass-card">
          <div class="glass-shine"></div>
          <div class="card-header">
            <span class="card-header-text">最近项目</span>
          </div>
          <div class="card-body">
            <el-table :data="recentProjects" size="small" v-loading="projectLoading" empty-text="暂无项目" class="dark-table">
              <el-table-column prop="id" label="ID" width="120" />
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="created_at" label="创建时间" width="180">
                <template #default="{ row }">
                  {{ formatTime(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Folder, Promotion, Monitor, Document, Plus } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { useGenerateStore } from '@/stores/generate'
import type { HealthResponse } from '@/api/generate'

const projectStore = useProjectStore()
const generateStore = useGenerateStore()

const projectCount = ref(0)
const todayCount = ref(0)
const modelStatus = ref('正常')
const recentCount = ref(0)
const healthInfo = ref<HealthResponse | null>(null)
const projectLoading = ref(false)
const recentProjects = ref<any[]>([])

const formatUptime = (seconds: number) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}小时${m}分钟`
}

const formatTime = (t: string) => {
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(async () => {
  projectLoading.value = true
  try {
    await projectStore.fetchProjects(0, 5)
    projectCount.value = projectStore.total
    recentProjects.value = projectStore.projects.slice(0, 5)
  } finally {
    projectLoading.value = false
  }

  try {
    const data = await generateStore.fetchHealth()
    healthInfo.value = data
    modelStatus.value = data.status === 'ok' ? '正常' : '异常'
  } catch {
    modelStatus.value = '异常'
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&display=swap');

.dashboard {
  padding: 0;
  font-family: 'Fira Sans', sans-serif;
  color: #F8FAFC;
}

.glass-card {
  position: relative;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

.glass-shine {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  z-index: 1;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 28px 20px 24px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.stat-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: #fff;
}

.stat-icon-blue {
  background: linear-gradient(135deg, #3B82F6, #1D4ED8);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
}

.stat-icon-green {
  background: linear-gradient(135deg, #38BDF8, #0EA5E9);
  box-shadow: 0 4px 16px rgba(34, 197, 94, 0.3);
}

.stat-icon-orange {
  background: linear-gradient(135deg, #F97316, #EA580C);
  box-shadow: 0 4px 16px rgba(249, 115, 22, 0.3);
}

.stat-icon-purple {
  background: linear-gradient(135deg, #A855F7, #7C3AED);
  box-shadow: 0 4px 16px rgba(168, 85, 247, 0.3);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #F8FAFC;
  line-height: 1.2;
  margin-bottom: 6px;
  font-family: 'Fira Sans', sans-serif;
}

.stat-title {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
}

.action-row {
  margin-bottom: 20px;
}

.card-header {
  padding: 18px 24px 0;
}

.card-header-text {
  font-size: 16px;
  font-weight: 600;
  color: #F8FAFC;
  font-family: 'Fira Sans', sans-serif;
}

.card-body {
  padding: 18px 24px 22px;
}

.glass-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  font-family: 'Fira Sans', sans-serif;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #F8FAFC;
  transition: all 0.25s ease;
  margin-right: 12px;
}

.glass-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.glass-btn-primary {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.3);
}

.glass-btn-primary:hover {
  background: rgba(59, 130, 246, 0.35);
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.25);
}

.glass-btn-cta {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.3);
}

.glass-btn-cta:hover {
  background: rgba(34, 197, 94, 0.35);
  border-color: rgba(34, 197, 94, 0.5);
  box-shadow: 0 4px 20px rgba(34, 197, 94, 0.25);
}

.info-row {
  margin-bottom: 20px;
}

:deep(.dark-descriptions) {
  --el-descriptions-table-border: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.dark-descriptions .el-descriptions__body) {
  background: transparent;
}

:deep(.dark-descriptions .el-descriptions__table) {
  background: transparent;
}

:deep(.dark-descriptions .el-descriptions__label) {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.6);
  font-family: 'Fira Sans', sans-serif;
}

:deep(.dark-descriptions .el-descriptions__content) {
  background: transparent;
  color: #F8FAFC;
  font-family: 'Fira Sans', sans-serif;
}

:deep(.dark-descriptions .el-descriptions__cell) {
  border-color: rgba(255, 255, 255, 0.08) !important;
}

:deep(.dark-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.06);
  --el-table-border-color: rgba(255, 255, 255, 0.08);
  --el-table-text-color: #F8FAFC;
  --el-table-header-text-color: rgba(255, 255, 255, 0.6);
}

:deep(.dark-table .el-table__inner-wrapper::before) {
  background-color: rgba(255, 255, 255, 0.08);
}

:deep(.dark-table .el-table__empty-text) {
  color: rgba(255, 255, 255, 0.4);
}

:deep(.dark-table th.el-table__cell) {
  background: rgba(255, 255, 255, 0.04) !important;
  font-family: 'Fira Sans', sans-serif;
  font-weight: 500;
}

:deep(.dark-table td.el-table__cell) {
  border-color: rgba(255, 255, 255, 0.08) !important;
  font-family: 'Fira Sans', sans-serif;
}

:deep(.el-tag--success) {
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.3);
  color: #38BDF8;
}

:deep(.el-tag--danger) {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: #EF4444;
}

:deep(.el-skeleton__item) {
  background: rgba(255, 255, 255, 0.06);
}

:deep(.el-loading-mask) {
  background: rgba(2, 6, 23, 0.6);
}

:deep(.el-loading-spinner .path) {
  stroke: #38BDF8;
}
</style>
