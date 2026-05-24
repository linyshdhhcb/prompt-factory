<template>
  <div class="model-manage">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>模型管理</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建模型
          </el-button>
        </div>
      </template>

      <el-table :data="models" v-loading="loading" stripe @row-click="showDetail">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" width="140" />
        <el-table-column prop="provider_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="providerTagType(row.provider_type)" size="small">
              {{ providerLabel(row.provider_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型" min-width="150" />
        <el-table-column prop="api_key_masked" label="API Key" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.api_key_masked === '****' ? 'info' : 'success'">
              {{ row.api_key_masked }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="success" size="small" link @click.stop="handleTest(row)" :loading="testingId === row.id">测试</el-button>
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模型' : '新建模型'" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="模型配置名称" />
        </el-form-item>
        <el-form-item label="Provider" prop="provider_type">
          <el-select v-model="form.provider_type" placeholder="选择 Provider 类型" style="width: 100%">
            <el-option label="OpenAI 兼容" value="openai" />
            <el-option label="Anthropic (Claude)" value="anthropic" />
            <el-option label="Azure OpenAI" value="azure" />
            <el-option label="Amazon Bedrock" value="bedrock" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            :placeholder="isEdit ? '留空则不修改' : '输入 API Key'"
            show-password
          />
        </el-form-item>
        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="API Base URL" />
        </el-form-item>
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="如 gpt-4o-mini, claude-3-5-sonnet-20241022" />
        </el-form-item>
        <el-form-item label="权重" prop="weight">
          <el-input-number v-model="form.weight" :min="0" :max="10" :step="0.1" />
        </el-form-item>
        <el-form-item label="最大Token" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="1" :max="128000" />
        </el-form-item>
        <el-form-item label="超时(s)" prop="timeout">
          <el-input-number v-model="form.timeout" :min="5" :max="300" />
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="模型详情" size="460px" direction="rtl">
      <el-descriptions :column="1" border v-if="detailData">
        <el-descriptions-item label="ID">{{ detailData.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="Provider">
          <el-tag :type="providerTagType(detailData.provider_type)" size="small">
            {{ providerLabel(detailData.provider_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="模型名称">{{ detailData.model_name }}</el-descriptions-item>
        <el-descriptions-item label="Base URL">{{ detailData.base_url }}</el-descriptions-item>
        <el-descriptions-item label="API Key">
          <el-tag size="small" :type="detailData.api_key_masked === '****' ? 'info' : 'success'">
            {{ detailData.api_key_masked }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="权重">{{ detailData.weight }}</el-descriptions-item>
        <el-descriptions-item label="最大Token">{{ detailData.max_tokens }}</el-descriptions-item>
        <el-descriptions-item label="超时(s)">{{ detailData.timeout }}</el-descriptions-item>
        <el-descriptions-item label="范围">
          <el-tag :type="detailData.scope === 'public' ? 'primary' : 'warning'" size="small">
            {{ detailData.scope === 'public' ? '公共' : '项目' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="项目ID">{{ detailData.project_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="启用">{{ detailData.enabled ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detailData.updated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import api from '@/api/index'

interface ModelItem {
  id: number
  name: string
  provider_type: string
  api_key_masked: string
  base_url: string
  model_name: string
  weight: number
  max_tokens: number
  timeout: number
  scope: string
  project_id: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

const providerLabel = (type: string) => {
  const map: Record<string, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    azure: 'Azure',
    bedrock: 'Bedrock',
  }
  return map[type] || type
}

const providerTagType = (type: string) => {
  const map: Record<string, string> = {
    openai: '',
    anthropic: 'success',
    azure: 'warning',
    bedrock: 'danger',
  }
  return map[type] || 'info'
}

const models = ref<ModelItem[]>([])
const total = ref(0)
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const testingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const detailVisible = ref(false)
const detailData = ref<ModelItem | null>(null)

const pageSize = 10
const currentPage = ref(1)

const form = reactive({
  name: '',
  provider_type: 'openai' as 'openai' | 'anthropic' | 'azure' | 'bedrock',
  api_key: '',
  base_url: '',
  model_name: '',
  weight: 1.0,
  max_tokens: 256,
  timeout: 30,
  scope: 'public' as 'public' | 'project',
  project_id: '',
  enabled: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  provider_type: [{ required: true, message: '请选择 Provider 类型', trigger: 'change' }],
  base_url: [{ required: true, message: '请输入Base URL', trigger: 'blur' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
}

const fetchModels = async (page?: number) => {
  loading.value = true
  try {
    const p = page ?? currentPage.value
    const { data } = await api.get('/api/v1/models', { params: { offset: (p - 1) * pageSize, limit: pageSize } })
    models.value = data.items ?? data
    total.value = data.total ?? 0
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchModels(page)
}

const showDetail = (row: ModelItem) => {
  detailData.value = row
  detailVisible.value = true
}

const showCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  form.name = ''
  form.provider_type = 'openai'
  form.api_key = ''
  form.base_url = ''
  form.model_name = ''
  form.weight = 1.0
  form.max_tokens = 256
  form.timeout = 30
  form.scope = 'public'
  form.project_id = ''
  form.enabled = true
  dialogVisible.value = true
}

const handleEdit = (row: ModelItem) => {
  isEdit.value = true
  editingId.value = row.id
  form.name = row.name
  form.provider_type = row.provider_type as 'openai' | 'anthropic' | 'azure' | 'bedrock'
  form.api_key = ''
  form.base_url = row.base_url
  form.model_name = row.model_name
  form.weight = row.weight
  form.max_tokens = row.max_tokens
  form.timeout = row.timeout
  form.scope = row.scope as 'public' | 'project'
  form.project_id = row.project_id || ''
  form.enabled = row.enabled
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const payload: any = {
      name: form.name,
      provider_type: form.provider_type,
      api_key: form.api_key,
      base_url: form.base_url,
      model_name: form.model_name,
      weight: form.weight,
      max_tokens: form.max_tokens,
      timeout: form.timeout,
      scope: form.scope,
      project_id: form.scope === 'project' ? form.project_id : null,
      enabled: form.enabled,
    }
    if (isEdit.value && editingId.value) {
      if (!form.api_key) {
        delete payload.api_key
      }
      await api.put(`/api/v1/models/${editingId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api/v1/models', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchModels()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await api.delete(`/api/v1/models/${id}`)
  ElMessage.success('已删除')
  fetchModels()
}

const handleToggle = async (row: ModelItem) => {
  await api.put(`/api/v1/models/${row.id}`, { enabled: row.enabled })
  ElMessage.success(row.enabled ? '已启用' : '已禁用')
}

const handleTest = async (row: ModelItem) => {
  testingId.value = row.id
  try {
    const { data } = await api.post(`/api/v1/models/${row.id}/test`)
    if (data.available) {
      ElMessage.success(`模型 ${row.name} 连通性测试通过`)
    } else {
      ElMessage.warning(`模型 ${row.name} 连通性测试失败`)
    }
  } catch {
    ElMessage.error(`模型 ${row.name} 连通性测试失败`)
  } finally {
    testingId.value = null
  }
}

onMounted(() => {
  fetchModels(1)
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
</style>
