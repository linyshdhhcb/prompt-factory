<template>
  <el-dialog v-model="visible" :title="editData ? '编辑人格' : '新建人格'" width="550px" destroy-on-close @close="handleClose">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="分类" prop="category">
        <el-select v-model="form.category" placeholder="选择分类" filterable allow-create style="width: 100%">
          <el-option v-for="c in commonCategories" :key="c" :label="c" :value="c" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签" prop="label">
        <el-input v-model="form.label" placeholder="人格标签" />
      </el-form-item>
      <el-form-item label="特征" prop="traits">
        <el-select v-model="form.traits" multiple filterable allow-create default-first-option placeholder="输入特征后回车" style="width: 100%">
        </el-select>
      </el-form-item>
      <el-form-item label="权重" prop="weight">
        <el-input-number v-model="form.weight" :min="0" :max="10" :step="0.1" />
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
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { usePersonaStore } from '@/stores/persona'
import type { PersonaTraitResponse } from '@/api/persona'

const props = defineProps<{
  visible: boolean
  editData: PersonaTraitResponse | null
  projectId?: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved'): void
}>()

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

import { computed } from 'vue'

const personaStore = usePersonaStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const commonCategories = ['语气', '情绪', '认知', '行为', '背景', '偏好']

const form = reactive({
  category: '',
  label: '',
  traits: [] as string[],
  weight: 1.0,
  scope: 'public' as 'public' | 'project',
  project_id: '',
})

const rules: FormRules = {
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  label: [{ required: true, message: '请输入标签', trigger: 'blur' }],
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (props.editData) {
        form.category = props.editData.category
        form.label = props.editData.label
        form.traits = Array.isArray(props.editData.traits) ? [...props.editData.traits] : []
        form.weight = props.editData.weight
        form.scope = props.editData.scope as 'public' | 'project'
        form.project_id = props.editData.project_id || ''
      } else {
        form.category = ''
        form.label = ''
        form.traits = []
        form.weight = 1.0
        form.scope = props.projectId ? 'project' : 'public'
        form.project_id = props.projectId || ''
      }
    }
  }
)

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const payload = {
      category: form.category,
      label: form.label,
      traits: form.traits,
      weight: form.weight,
      scope: form.scope,
      project_id: form.scope === 'project' ? form.project_id || null : null,
    }
    if (props.editData) {
      await personaStore.editTrait(props.editData.id, payload)
      ElMessage.success('更新成功')
    } else {
      await personaStore.addTrait(payload)
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
