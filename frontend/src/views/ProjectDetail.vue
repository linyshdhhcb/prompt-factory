<template>
  <div class="project-detail" v-loading="projectStore.loading">
    <el-page-header @back="$router.push('/projects')" class="page-header">
      <template #content>
        <span>{{ projectStore.currentProject?.name || '项目详情' }}</span>
      </template>
    </el-page-header>

    <el-tabs v-model="activeTab" class="detail-tabs" v-if="projectStore.currentProject">
      <el-tab-pane label="概览" name="overview">
        <el-card shadow="never">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目ID">{{ projectStore.currentProject.id }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ projectStore.currentProject.name }}</el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">{{ projectStore.currentProject.description || '无' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatTime(projectStore.currentProject.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatTime(projectStore.currentProject.updated_at) }}</el-descriptions-item>
            <el-descriptions-item label="配置" :span="2">
              <el-input
                type="textarea"
                :rows="6"
                :model-value="JSON.stringify(projectStore.currentProject.config, null, 2)"
                readonly
              />
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="人格" name="persona">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>人格配置</span>
              <el-button type="primary" size="small" @click="showPersonaDialog = true">添加人格</el-button>
            </div>
          </template>
          <div v-if="personaPreview" class="persona-preview">
            <pre>{{ JSON.stringify(personaPreview, null, 2) }}</pre>
          </div>
          <el-empty v-else description="暂无人格配置" />
        </el-card>

        <PersonaEditor
          v-model:visible="showPersonaDialog"
          :edit-data="null"
          :project-id="projectId"
          @saved="handlePersonaSaved"
        />
      </el-tab-pane>

      <el-tab-pane label="生成" name="generate">
        <GeneratePanel :project-id="projectId" />
      </el-tab-pane>

      <el-tab-pane label="历史记录" name="history">
        <HistoryView :project-id="projectId" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { usePersonaStore } from '@/stores/persona'
import GeneratePanel from '@/components/GeneratePanel.vue'
import HistoryView from '@/components/HistoryView.vue'
import PersonaEditor from '@/components/PersonaEditor.vue'

const route = useRoute()
const projectStore = useProjectStore()
const personaStore = usePersonaStore()

const projectId = route.params.id as string
const activeTab = ref('overview')
const showPersonaDialog = ref(false)
const personaPreview = ref<Record<string, any> | null>(null)

const formatTime = (t: string) => new Date(t).toLocaleString('zh-CN')

const handlePersonaSaved = () => {
  loadPersonaPreview()
}

const loadPersonaPreview = async () => {
  try {
    const data = await personaStore.fetchPreview(projectId)
    personaPreview.value = data as any
  } catch {
    personaPreview.value = null
  }
}

watch(activeTab, (val) => {
  if (val === 'persona') {
    loadPersonaPreview()
  }
})

onMounted(() => {
  projectStore.fetchProject(projectId)
})
</script>

<style scoped>
:deep(.el-card) { background: rgba(255,255,255,0.06); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; color: #F8FAFC; }
:deep(.el-card__header) { border-bottom: 1px solid rgba(255,255,255,0.1); color: #F8FAFC; }
:deep(.el-table) { --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: rgba(255,255,255,0.08); --el-table-row-hover-bg-color: rgba(255,255,255,0.05); --el-table-text-color: #F8FAFC; --el-table-header-text-color: rgba(255,255,255,0.7); --el-table-border-color: rgba(255,255,255,0.08); }
:deep(.el-dialog) { background: #1E293B; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; }
:deep(.el-dialog__title) { color: #F8FAFC; }
:deep(.el-form-item__label) { color: rgba(255,255,255,0.7); }
:deep(.el-input__wrapper) { background: rgba(255,255,255,0.08); box-shadow: none; border: 1px solid rgba(255,255,255,0.1); }
:deep(.el-input__inner) { color: #F8FAFC; }
:deep(.el-select) { --el-select-border-color-hover: rgba(255,255,255,0.2); }
:deep(.el-button--primary) { --el-button-bg-color: #38BDF8; --el-button-border-color: #38BDF8; }
:deep(.el-textarea__inner) { background: rgba(255,255,255,0.08); color: #F8FAFC; border: 1px solid rgba(255,255,255,0.1); }
:deep(.el-switch) { --el-switch-on-color: #38BDF8; }
:deep(.el-tag) { border-color: rgba(255,255,255,0.1); }
:deep(.el-descriptions) { --el-descriptions-table-border: 1px solid rgba(255,255,255,0.08); }
:deep(.el-descriptions__label) { color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.04); }
:deep(.el-descriptions__content) { color: #F8FAFC; }
:deep(.el-skeleton__item) { background: rgba(255,255,255,0.08); }
:deep(.el-loading-mask) { background: rgba(2,6,23,0.7); }
:deep(.el-popconfirm__main) { color: #F8FAFC; }
:deep(.el-input-number) { --el-input-number-unit-offset-x: 0; }
:deep(.el-radio__label) { color: rgba(255,255,255,0.7); }
:deep(.el-pagination) { --el-pagination-bg-color: transparent; --el-pagination-text-color: rgba(255,255,255,0.7); --el-pagination-button-bg-color: rgba(255,255,255,0.08); }
.card-header { display: flex; justify-content: space-between; align-items: center; color: #F8FAFC; }

.page-header {
  margin-bottom: 20px;
}

.detail-tabs {
  margin-top: 10px;
}

.persona-preview pre {
  background: rgba(255,255,255,0.06);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  color: #F8FAFC;
}
</style>
