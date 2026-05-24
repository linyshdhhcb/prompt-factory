import api from './index'

export interface GenerateRequest {
  project_id: string
  task_domain: string
  count: number
  human_likeness: 'low' | 'medium' | 'high' | 'insane'
  source_models?: string[]
  similarity_threshold?: number | null
  extra_params?: Record<string, any>
}

export interface PromptResponse {
  id: string
  project_id: string
  text: string
  persona_snapshot: Record<string, any>
  source_model: string | null
  dedup_skipped: boolean
  task_domain: string | null
  created_at: string
}

export interface GenerationMeta {
  count: number
  task_domain: string
  human_likeness: string
  elapsed_seconds: number
}

export interface GenerateResponse {
  prompts: PromptResponse[]
  meta: GenerationMeta
}

export interface GenerateAsyncResponse {
  task_id: string
  status: string
}

export interface GenerateProgress {
  task_id: string
  status: string
  progress: number
  completed: number
  total: number
  result: GenerateResponse | null
}

export interface HistoryResponse {
  items: PromptResponse[]
  total: number
  page: number
  page_size: number
}

export interface HealthResponse {
  status: string
  version: string
  uptime_seconds: number
}

export const generateSync = (data: GenerateRequest) =>
  api.post<GenerateResponse>('/api/v1/generate', data)

export const generateAsync = (data: GenerateRequest) =>
  api.post<GenerateAsyncResponse>('/api/v1/generate/async', data)

export const getTaskStatus = (taskId: string) =>
  api.get<GenerateProgress>(`/api/v1/generate/${taskId}`)

export const getHistory = (projectId: string, params?: { page?: number; page_size?: number }) =>
  api.get<HistoryResponse>(`/api/v1/history/${projectId}`, { params })

export const deleteProjectPrompts = (projectId: string) =>
  api.delete(`/api/v1/project/${projectId}`)

export const healthCheck = () =>
  api.get<HealthResponse>('/api/v1/health')
