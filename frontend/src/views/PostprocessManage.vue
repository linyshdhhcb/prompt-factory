<template>
  <div class="postprocess-manage">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>后处理规则</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建规则
          </el-button>
        </div>
      </template>

      <el-table :data="rules" v-loading="loading" stripe @row-click="showDetail">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="sort_order" label="排序" width="70" />
        <el-table-column prop="name" label="名称" min-width="130" />
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column prop="probability" label="概率" width="100" />
        <el-table-column prop="enabled" label="启用" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="scope" label="范围" width="80">
          <template #default="{ row }">
            <el-tag :type="row.scope === 'public' ? 'primary' : 'warning'" size="small">
              {{ row.scope === 'public' ? '公共' : '项目' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row, $index }">
            <el-button size="small" link :disabled="$index === 0" @click.stop="moveUp($index)">上移</el-button>
            <el-button size="small" link :disabled="$index === rules.length - 1" @click.stop="moveDown($index)">下移</el-button>
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

    <RuleEditor
      v-model:visible="dialogVisible"
      :edit-data="editingRule"
      @saved="handleSaved"
    />

    <el-drawer v-model="detailVisible" title="规则详情" size="460px" direction="rtl">
      <el-descriptions :column="1" border v-if="detailData">
        <el-descriptions-item label="ID">{{ detailData.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ detailData.description }}</el-descriptions-item>
        <el-descriptions-item label="排序">{{ detailData.sort_order }}</el-descriptions-item>
        <el-descriptions-item label="触发概率">{{ detailData.probability }}</el-descriptions-item>
        <el-descriptions-item label="启用">{{ detailData.enabled ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="范围">
          <el-tag :type="detailData.scope === 'public' ? 'primary' : 'warning'" size="small">
            {{ detailData.scope === 'public' ? '公共' : '项目' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="项目ID">{{ detailData.project_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="参数">
          <pre class="params-json">{{ JSON.stringify(detailData.params, null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detailData.updated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api/index'
import RuleEditor from '@/components/RuleEditor.vue'

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

const rules = ref<RuleItem[]>([])
const total = ref(0)
const loading = ref(false)
const dialogVisible = ref(false)
const editingRule = ref<RuleItem | null>(null)
const detailVisible = ref(false)
const detailData = ref<RuleItem | null>(null)

const pageSize = 10
const currentPage = ref(1)

const fetchRules = async (page?: number) => {
  loading.value = true
  try {
    const p = page ?? currentPage.value
    const { data } = await api.get('/api/v1/postprocess/rules', { params: { offset: (p - 1) * pageSize, limit: pageSize } })
    const items = data.items ?? data
    rules.value = items.sort((a: RuleItem, b: RuleItem) => a.sort_order - b.sort_order)
    total.value = data.total ?? 0
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchRules(page)
}

const showDetail = (row: RuleItem) => {
  detailData.value = row
  detailVisible.value = true
}

const showCreateDialog = () => {
  editingRule.value = null
  dialogVisible.value = true
}

const handleEdit = (row: RuleItem) => {
  editingRule.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (id: number) => {
  await api.delete(`/api/v1/postprocess/rules/${id}`)
  ElMessage.success('已删除')
  fetchRules()
}

const handleToggle = async (row: RuleItem) => {
  await api.put(`/api/v1/postprocess/rules/${row.id}`, { enabled: row.enabled })
  ElMessage.success(row.enabled ? '已启用' : '已禁用')
}

const moveUp = async (index: number) => {
  if (index <= 0) return
  const list = [...rules.value]
  const temp = list[index]
  list[index] = list[index - 1]
  list[index - 1] = temp
  await updateSortOrder(list)
}

const moveDown = async (index: number) => {
  if (index >= rules.value.length - 1) return
  const list = [...rules.value]
  const temp = list[index]
  list[index] = list[index + 1]
  list[index + 1] = temp
  await updateSortOrder(list)
}

const updateSortOrder = async (list: RuleItem[]) => {
  const items = list.map((r, i) => ({ id: r.id, sort_order: i }))
  try {
    await api.put('/api/v1/postprocess/rules/sort', { items })
    rules.value = list.map((r, i) => ({ ...r, sort_order: i }))
    ElMessage.success('排序已更新')
  } catch {
    fetchRules()
  }
}

const handleSaved = () => {
  fetchRules()
}

onMounted(() => {
  fetchRules(1)
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
.params-json { margin: 0; font-size: 12px; color: #38BDF8; white-space: pre-wrap; word-break: break-all; }
</style>
