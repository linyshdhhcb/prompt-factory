import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  generateSync,
  generateAsync,
  getTaskStatus,
  getHistory,
  deleteProjectPrompts,
  healthCheck,
  type GenerateProgress,
  type HistoryResponse,
  type HealthResponse,
  type GenerateRequest,
} from '@/api/generate'

export const useGenerateStore = defineStore('generate', () => {
  const generating = ref(false)
  const progress = ref<GenerateProgress | null>(null)
  const history = ref<HistoryResponse | null>(null)
  const health = ref<HealthResponse | null>(null)
  const loadingHistory = ref(false)
  let eventSource: EventSource | null = null

  const startSync = async (payload: GenerateRequest) => {
    generating.value = true
    try {
      const { data } = await generateSync(payload)
      return data
    } finally {
      generating.value = false
    }
  }

  const startAsync = async (payload: GenerateRequest) => {
    generating.value = true
    progress.value = null
    const { data } = await generateAsync(payload)
    connectSSE(data.task_id)
    return data
  }

  const connectSSE = (taskId: string) => {
    if (eventSource) {
      eventSource.close()
    }
    eventSource = new EventSource(`/api/v1/generate/${taskId}/stream`)
    eventSource.onmessage = (event) => {
      const data: GenerateProgress = JSON.parse(event.data)
      progress.value = data
      if (data.status === 'completed' || data.status === 'failed') {
        generating.value = false
        eventSource?.close()
        eventSource = null
      }
    }
    eventSource.onerror = () => {
      eventSource?.close()
      eventSource = null
      generating.value = false
    }
  }

  const pollTaskStatus = async (taskId: string) => {
    const { data } = await getTaskStatus(taskId)
    progress.value = data
    if (data.status === 'completed' || data.status === 'failed') {
      generating.value = false
    }
    return data
  }

  const fetchHistory = async (projectId: string, page = 1, pageSize = 20) => {
    loadingHistory.value = true
    try {
      const { data } = await getHistory(projectId, { page, page_size: pageSize })
      history.value = data
    } finally {
      loadingHistory.value = false
    }
  }

  const clearHistory = async (projectId: string) => {
    await deleteProjectPrompts(projectId)
    history.value = null
  }

  const fetchHealth = async () => {
    const { data } = await healthCheck()
    health.value = data
    return data
  }

  const resetProgress = () => {
    progress.value = null
    generating.value = false
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  return {
    generating,
    progress,
    history,
    health,
    loadingHistory,
    startSync,
    startAsync,
    pollTaskStatus,
    fetchHistory,
    clearHistory,
    fetchHealth,
    resetProgress,
  }
})
