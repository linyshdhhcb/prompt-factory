<template>
  <div class="history-view">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>生成历史</span>
          <div>
            <el-button @click="loadHistory" :loading="generateStore.loadingHistory">刷新</el-button>
            <el-popconfirm title="确定清空所有历史记录？" @confirm="handleClear">
              <template #reference>
                <el-button type="danger">清空历史</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </template>

      <el-table :data="generateStore.history?.items ?? []" v-loading="generateStore.loadingHistory" stripe>
        <el-table-column prop="id" label="ID" width="280" show-overflow-tooltip />
        <el-table-column prop="text" label="内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="source_model" label="源模型" width="120" />
        <el-table-column prop="task_domain" label="任务域" width="120" />
        <el-table-column prop="dedup_skipped" label="去重跳过" width="90">
          <template #default="{ row }">
            <el-tag :type="row.dedup_skipped ? 'warning' : 'success'" size="small">
              {{ row.dedup_skipped ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="(generateStore.history?.total ?? 0) > pageSize"
        class="pagination"
        layout="total, prev, pager, next"
        :total="generateStore.history?.total ?? 0"
        :page-size="pageSize"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useGenerateStore } from '@/stores/generate'

const props = defineProps<{
  projectId: string
}>()

const generateStore = useGenerateStore()
const pageSize = 20
const currentPage = ref(1)

const formatTime = (t: string) => new Date(t).toLocaleString('zh-CN')

const loadHistory = () => {
  generateStore.fetchHistory(props.projectId, currentPage.value, pageSize)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadHistory()
}

const handleClear = async () => {
  await generateStore.clearHistory(props.projectId)
  ElMessage.success('历史记录已清空')
}

onMounted(() => {
  loadHistory()
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

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
