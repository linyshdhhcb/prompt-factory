<template>
  <div class="generate-panel">
    <el-card shadow="never">
      <template #header>
        <span>生成配置</span>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="任务域" prop="task_domain">
          <el-input v-model="form.task_domain" placeholder="如：客服对话、社交媒体" />
        </el-form-item>
        <el-form-item label="生成数量" prop="count">
          <el-input-number v-model="form.count" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="拟人程度" prop="human_likeness">
          <el-select v-model="form.human_likeness" placeholder="选择拟人程度">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="极高" value="insane" />
          </el-select>
        </el-form-item>
        <el-form-item label="源模型" prop="source_models">
          <el-select v-model="form.source_models" multiple placeholder="选择源模型（可多选）" style="width: 100%">
            <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="相似度阈值" prop="similarity_threshold">
          <el-input-number v-model="form.similarity_threshold" :min="0" :max="1" :step="0.01" :precision="2" placeholder="留空使用默认值" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleGenerate" :loading="generateStore.generating">
            <el-icon><Promotion /></el-icon>
            开始生成
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <ProgressMonitor v-if="generateStore.generating || generateStore.progress" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Promotion } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useGenerateStore } from '@/stores/generate'
import api from '@/api/index'
import ProgressMonitor from './ProgressMonitor.vue'

const props = defineProps<{
  projectId: string
}>()

const generateStore = useGenerateStore()
const formRef = ref<FormInstance>()

interface ModelOption {
  id: number
  name: string
}

const modelOptions = ref<ModelOption[]>([])

const form = reactive({
  task_domain: '',
  count: 10,
  human_likeness: 'medium' as 'low' | 'medium' | 'high' | 'insane',
  source_models: [] as string[],
  similarity_threshold: null as number | null,
})

const rules: FormRules = {
  task_domain: [{ required: true, message: '请输入任务域', trigger: 'blur' }],
  count: [{ required: true, message: '请输入生成数量', trigger: 'blur' }],
  human_likeness: [{ required: true, message: '请选择拟人程度', trigger: 'change' }],
}

const fetchModels = async () => {
  try {
    const { data } = await api.get('/api/v1/models')
    const list = data.items ?? data
    modelOptions.value = list.filter((m: any) => m.enabled)
  } catch {}
}

const handleGenerate = async () => {
  await formRef.value?.validate()
  generateStore.resetProgress()

  try {
    await generateStore.startAsync({
      project_id: props.projectId,
      task_domain: form.task_domain,
      count: form.count,
      human_likeness: form.human_likeness,
      source_models: form.source_models,
      similarity_threshold: form.similarity_threshold,
    })
    ElMessage.success('生成任务已提交')
  } catch {
    ElMessage.error('生成任务提交失败')
  }
}

onMounted(() => {
  fetchModels()
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

.generate-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
