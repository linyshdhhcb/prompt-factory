<template>
  <div class="progress-monitor">
    <el-card shadow="never">
      <template #header>
        <span>生成进度</span>
      </template>

      <el-progress
        :percentage="progressPercent"
        :status="progressStatus"
        :stroke-width="20"
        :text-inside="true"
      />

      <div class="progress-info">
        <span v-if="generateStore.progress">
          状态：{{ statusText }} | 已完成：{{ generateStore.progress.completed }} / {{ generateStore.progress.total }}
        </span>
        <span v-else>
          正在连接...
        </span>
      </div>

      <div v-if="generateStore.progress?.status === 'completed'" class="progress-result">
        <el-tag type="success" size="large">生成完成</el-tag>
        <span v-if="generateStore.progress.result">
          共生成 {{ generateStore.progress.result.prompts?.length ?? 0 }} 条，耗时 {{ generateStore.progress.result.meta?.elapsed_seconds?.toFixed(1) ?? '-' }}秒
        </span>
      </div>

      <div v-if="generateStore.progress?.status === 'failed'" class="progress-result">
        <el-tag type="danger" size="large">生成失败</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGenerateStore } from '@/stores/generate'

const generateStore = useGenerateStore()

const progressPercent = computed(() => {
  if (!generateStore.progress) return 0
  if (generateStore.progress.status === 'completed') return 100
  return Math.round(generateStore.progress.progress * 100)
})

const progressStatus = computed(() => {
  if (!generateStore.progress) return undefined
  if (generateStore.progress.status === 'completed') return 'success' as const
  if (generateStore.progress.status === 'failed') return 'exception' as const
  return undefined
})

const statusText = computed(() => {
  if (!generateStore.progress) return '等待中'
  const map: Record<string, string> = {
    pending: '等待中',
    running: '生成中',
    completed: '已完成',
    failed: '失败',
  }
  return map[generateStore.progress.status] ?? generateStore.progress.status
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

.progress-monitor {
  margin-top: 16px;
}

.progress-info {
  margin-top: 12px;
  font-size: 14px;
  color: rgba(255,255,255,0.7);
}

.progress-result {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
