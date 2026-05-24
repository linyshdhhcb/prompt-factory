<template>
  <div class="template-manage">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>模板管理</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建模板
          </el-button>
        </div>
      </template>

      <el-table :data="templates" v-loading="loading" stripe @row-click="showDetail">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="template" label="模板内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="scope" label="范围" width="90">
          <template #default="{ row }">
            <el-tag :type="row.scope === 'public' ? 'primary' : 'warning'" size="small">
              {{ row.scope === 'public' ? '公共' : '项目' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="weight" label="权重" width="70" />
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click.stop="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" size="small" link @click.stop>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模板' : '新建模板'" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="模板内容" prop="template">
          <el-input v-model="form.template" type="textarea" :rows="8" placeholder="输入模板文本" />
        </el-form-item>
        <el-form-item label="范围" prop="scope">
          <el-radio-group v-model="form.scope">
            <el-radio value="public">公共</el-radio>
            <el-radio value="project">项目</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="项目ID" prop="project_id" v-if="form.scope === 'project'">
          <el-input v-model="form.project_id" placeholder="关联项目ID" />
        </el-form-item>
        <el-form-item label="权重" prop="weight">
          <el-input-number v-model="form.weight" :min="0" :max="10" :step="0.1" />
        </el-form-item>
        <el-form-item label="启用" prop="enabled">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="模板详情" size="520px" direction="rtl">
      <el-descriptions :column="1" border v-if="detailData">
        <el-descriptions-item label="ID">{{ detailData.id }}</el-descriptions-item>
        <el-descriptions-item label="范围">
          <el-tag :type="detailData.scope === 'public' ? 'primary' : 'warning'" size="small">
            {{ detailData.scope === 'public' ? '公共' : '项目' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="项目ID">{{ detailData.project_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="权重">{{ detailData.weight }}</el-descriptions-item>
        <el-descriptions-item label="启用">{{ detailData.enabled ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="模板内容">
          <pre class="template-content">{{ detailData.template }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import api from '@/api/index'

interface TemplateItem {
  id: number
  template: string
  scope: string
  project_id: string | null
  enabled: boolean
  weight: number
  created_at: string
}

const templates = ref<TemplateItem[]>([])
const total = ref(0)
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const detailVisible = ref(false)
const detailData = ref<TemplateItem | null>(null)

const pageSize = 10
const currentPage = ref(1)

const form = reactive({
  template: '',
  scope: 'public' as 'public' | 'project',
  project_id: '',
  weight: 1.0,
  enabled: true,
})

const rules: FormRules = {
  template: [{ required: true, message: '请输入模板内容', trigger: 'blur' }],
}

const fetchTemplates = async (page?: number) => {
  loading.value = true
  try {
    const p = page ?? currentPage.value
    const { data } = await api.get('/api/v1/meta-templates', { params: { offset: (p - 1) * pageSize, limit: pageSize } })
    templates.value = data.items ?? data
    total.value = data.total ?? 0
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchTemplates(page)
}

const showDetail = (row: TemplateItem) => {
  detailData.value = row
  detailVisible.value = true
}

const showCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  form.template = ''
  form.scope = 'public'
  form.project_id = ''
  form.weight = 1.0
  form.enabled = true
  dialogVisible.value = true
}

const handleEdit = (row: TemplateItem) => {
  isEdit.value = true
  editingId.value = row.id
  form.template = row.template
  form.scope = row.scope as 'public' | 'project'
  form.project_id = row.project_id || ''
  form.weight = row.weight
  form.enabled = row.enabled
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const payload: any = {
      template: form.template,
      scope: form.scope,
      weight: form.weight,
      enabled: form.enabled,
      project_id: form.scope === 'project' ? form.project_id : null,
    }
    if (isEdit.value && editingId.value) {
      await api.put(`/api/v1/meta-templates/${editingId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api/v1/meta-templates', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchTemplates()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await api.delete(`/api/v1/meta-templates/${id}`)
  ElMessage.success('已删除')
  fetchTemplates()
}

const handleToggle = async (row: TemplateItem) => {
  await api.put(`/api/v1/meta-templates/${row.id}`, { enabled: row.enabled })
  ElMessage.success(row.enabled ? '已启用' : '已禁用')
}

onMounted(() => {
  fetchTemplates(1)
})
</script>

<style scoped>
:deep(.el-card) { background: rgba(255,255,255,0.06); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; color: #F8FAFC; }
:deep(.el-card__header) { border-bottom: 1px solid rgba(255,255,255,0.1); color: #F8FAFC; }
:deep(.el-table) { --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: rgba(255,255,255,0.08); --el-table-row-hover-bg-color: rgba(255,255,255,0.05); --el-table-text-color: #F8FAFC; --el-table-header-text-color: rgba(255,255,255,0.7); --el-table-border-color: rgba(255,255,255,0.08); cursor: pointer; }
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
:deep(.el-drawer) { background: #1E293B; }
:deep(.el-drawer__header) { color: #F8FAFC; }
:deep(.el-drawer__body) { color: #F8FAFC; }
.card-header { display: flex; justify-content: space-between; align-items: center; color: #F8FAFC; }
.pagination { margin-top: 16px; justify-content: flex-end; }
.template-content { margin: 0; font-size: 13px; color: #38BDF8; white-space: pre-wrap; word-break: break-all; line-height: 1.6; }
</style>
