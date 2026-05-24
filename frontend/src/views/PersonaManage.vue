<template>
  <div class="persona-manage">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>人格管理</span>
          <div class="header-actions">
            <el-select v-model="filterCategory" placeholder="分类筛选" clearable style="width: 150px; margin-right: 12px" @change="handleFilter">
              <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
            </el-select>
            <el-input v-model="searchText" placeholder="搜索标签" clearable style="width: 200px; margin-right: 12px" @input="handleSearch" />
            <el-upload
              :show-file-list="false"
              :before-upload="handleImport"
              accept=".yaml,.yml,.json"
            >
              <el-button type="warning">批量导入</el-button>
            </el-upload>
            <el-button type="primary" @click="showCreateDialog">
              <el-icon><Plus /></el-icon>
              新建人格
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredTraits" v-loading="personaStore.loading" stripe @row-click="showDetail">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="label" label="标签" min-width="140" />
        <el-table-column prop="weight" label="权重" width="80" />
        <el-table-column prop="scope" label="范围" width="90">
          <template #default="{ row }">
            <el-tag :type="row.scope === 'public' ? 'primary' : 'warning'" size="small">
              {{ row.scope === 'public' ? '公共' : '项目' }}
            </el-tag>
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
        :total="personaStore.total"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
      />
    </el-card>

    <PersonaEditor
      v-model:visible="dialogVisible"
      :edit-data="editingTrait"
      @saved="handleSaved"
    />

    <el-drawer v-model="detailVisible" title="人格详情" size="420px" direction="rtl">
      <el-descriptions :column="1" border v-if="detailData">
        <el-descriptions-item label="ID">{{ detailData.id }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ detailData.category }}</el-descriptions-item>
        <el-descriptions-item label="标签">{{ detailData.label }}</el-descriptions-item>
        <el-descriptions-item label="权重">{{ detailData.weight }}</el-descriptions-item>
        <el-descriptions-item label="范围">
          <el-tag :type="detailData.scope === 'public' ? 'primary' : 'warning'" size="small">
            {{ detailData.scope === 'public' ? '公共' : '项目' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="项目ID">{{ detailData.project_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="特征列表">
          <div class="trait-tags">
            <el-tag v-for="(t, i) in (Array.isArray(detailData.traits) ? detailData.traits : [])" :key="i" size="small" style="margin: 2px 4px 2px 0">{{ t }}</el-tag>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detailData.updated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { usePersonaStore } from '@/stores/persona'
import PersonaEditor from '@/components/PersonaEditor.vue'
import type { PersonaTraitResponse } from '@/api/persona'

const personaStore = usePersonaStore()

const pageSize = 10
const currentPage = ref(1)
const filterCategory = ref('')
const searchText = ref('')
const dialogVisible = ref(false)
const editingTrait = ref<PersonaTraitResponse | null>(null)
const detailVisible = ref(false)
const detailData = ref<PersonaTraitResponse | null>(null)

const categories = ['occupation', 'mood', 'language_habit', 'typing_habit', 'scene', 'education']

const filteredTraits = computed(() => {
  if (!searchText.value) return personaStore.traits
  const s = searchText.value.toLowerCase()
  return personaStore.traits.filter((t) => t.label.toLowerCase().includes(s))
})

const showDetail = (row: PersonaTraitResponse) => {
  detailData.value = row
  detailVisible.value = true
}

const showCreateDialog = () => {
  editingTrait.value = null
  dialogVisible.value = true
}

const handleEdit = (row: PersonaTraitResponse) => {
  editingTrait.value = row
  dialogVisible.value = true
}

const handleDelete = async (id: number) => {
  await personaStore.removeTrait(id)
  ElMessage.success('已删除')
}

const buildFetchParams = (page?: number) => {
  const p: { offset: number; limit: number; category?: string } = {
    offset: ((page ?? currentPage.value) - 1) * pageSize,
    limit: pageSize,
  }
  if (filterCategory.value) p.category = filterCategory.value
  return p
}

const handleFilter = () => {
  currentPage.value = 1
  personaStore.fetchTraits(buildFetchParams(1))
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    personaStore.fetchTraits(buildFetchParams(1))
  }, 300)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  personaStore.fetchTraits(buildFetchParams(page))
}

const handleImport = async (file: UploadFile) => {
  if (!file.raw) return false
  const formData = new FormData()
  formData.append('file', file.raw)
  try {
    await personaStore.importFromFile(formData)
    ElMessage.success('导入成功')
    personaStore.fetchTraits(buildFetchParams(1))
  } catch {
    ElMessage.error('导入失败')
  }
  return false
}

const handleSaved = () => {
  personaStore.fetchTraits(buildFetchParams())
}

onMounted(() => {
  personaStore.fetchTraits(buildFetchParams(1))
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
.header-actions { display: flex; align-items: center; }
.pagination { margin-top: 16px; justify-content: flex-end; }
.trait-tags { display: flex; flex-wrap: wrap; }
</style>
