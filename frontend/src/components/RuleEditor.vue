<template>
  <el-dialog v-model="visible" :title="editData ? '编辑规则' : '新建规则'" width="600px" destroy-on-close @close="handleClose">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="规则名称" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="2" placeholder="规则描述" />
      </el-form-item>
      <el-form-item label="概率" prop="probability">
        <el-slider v-model="form.probability" :min="0" :max="1" :step="0.01" show-input />
      </el-form-item>
      <el-form-item label="参数" prop="params">
        <el-input v-model="form.paramsStr" type="textarea" :rows="4" placeholder="JSON 格式参数" />
      </el-form-item>
      <el-form-item label="范围" prop="scope">
        <el-radio-group v-model="form.scope">
          <el-radio value="public">公共</el-radio>
          <el-radio value="project">项目</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="项目ID" v-if="form.scope === 'project'">
        <el-input v-model="form.project_id" placeholder="关联项目ID" />
      </el-form-item>
      <el-form-item label="启用" prop="enabled">
        <el-switch v-model="form.enabled" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import api from '@/api/index'

interface RuleItem {
  id: number
  name: string
  description: string
  probability: number
  params: Record<string, any>
  scope: string
  project_id: string | null
  enabled: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

const props = defineProps<{
  visible: boolean
  editData: RuleItem | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved'): void
}>()

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  name: '',
  description: '',
  probability: 0.1,
  paramsStr: '{}',
  scope: 'public' as 'public' | 'project',
  project_id: '',
  enabled: true,
})

const validateParams = (_rule: any, value: string, callback: any) => {
  try {
    JSON.parse(form.paramsStr)
    callback()
  } catch {
    callback(new Error('请输入有效的JSON'))
  }
}

const rules: FormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  paramsStr: [{ validator: validateParams, trigger: 'blur' }],
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (props.editData) {
        form.name = props.editData.name
        form.description = props.editData.description
        form.probability = props.editData.probability
        form.paramsStr = JSON.stringify(props.editData.params, null, 2)
        form.scope = props.editData.scope as 'public' | 'project'
        form.project_id = props.editData.project_id || ''
        form.enabled = props.editData.enabled
      } else {
        form.name = ''
        form.description = ''
        form.probability = 0.1
        form.paramsStr = '{}'
        form.scope = 'public'
        form.project_id = ''
        form.enabled = true
      }
    }
  }
)

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    let params: Record<string, any>
    try {
      params = JSON.parse(form.paramsStr)
    } catch {
      ElMessage.error('参数JSON格式错误')
      return
    }
    const payload = {
      name: form.name,
      description: form.description,
      probability: form.probability,
      params,
      scope: form.scope,
      project_id: form.scope === 'project' ? form.project_id || null : null,
      enabled: form.enabled,
    }
    if (props.editData) {
      await api.put(`/api/v1/postprocess/rules/${props.editData.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api/v1/postprocess/rules', payload)
      ElMessage.success('创建成功')
    }
    emit('saved')
    visible.value = false
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  visible.value = false
}
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
</style>
