import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  listProjects,
  createProject,
  getProject,
  updateProject,
  deleteProject,
  type ProjectResponse,
  type ProjectCreate,
  type ProjectUpdate,
} from '@/api/project'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<ProjectResponse[]>([])
  const currentProject = ref<ProjectResponse | null>(null)
  const total = ref(0)
  const loading = ref(false)

  const fetchProjects = async (skip = 0, limit = 20) => {
    loading.value = true
    try {
      const { data } = await listProjects({ skip, limit })
      projects.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  const fetchProject = async (id: string) => {
    loading.value = true
    try {
      const { data } = await getProject(id)
      currentProject.value = data
    } finally {
      loading.value = false
    }
  }

  const addProject = async (payload: ProjectCreate) => {
    const { data } = await createProject(payload)
    projects.value.unshift(data)
    total.value += 1
    return data
  }

  const editProject = async (id: string, payload: ProjectUpdate) => {
    const { data } = await updateProject(id, payload)
    const idx = projects.value.findIndex((p) => p.id === id)
    if (idx !== -1) projects.value[idx] = data
    if (currentProject.value?.id === id) currentProject.value = data
    return data
  }

  const removeProject = async (id: string) => {
    await deleteProject(id)
    projects.value = projects.value.filter((p) => p.id !== id)
    total.value -= 1
    if (currentProject.value?.id === id) currentProject.value = null
  }

  return {
    projects,
    currentProject,
    total,
    loading,
    fetchProjects,
    fetchProject,
    addProject,
    editProject,
    removeProject,
  }
})
