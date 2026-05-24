import api from './index'

export interface ProjectCreate {
  name: string
  description?: string
  config?: Record<string, any>
}

export interface ProjectUpdate {
  name?: string
  description?: string
  config?: Record<string, any>
}

export interface ProjectResponse {
  id: string
  name: string
  description: string
  config: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  items: ProjectResponse[]
  total: number
}

export const listProjects = (params?: { skip?: number; limit?: number }) =>
  api.get<ProjectListResponse>('/api/v1/projects', { params })

export const createProject = (data: ProjectCreate) =>
  api.post<ProjectResponse>('/api/v1/projects', data)

export const getProject = (id: string) =>
  api.get<ProjectResponse>(`/api/v1/projects/${id}`)

export const updateProject = (id: string, data: ProjectUpdate) =>
  api.put<ProjectResponse>(`/api/v1/projects/${id}`, data)

export const deleteProject = (id: string) =>
  api.delete(`/api/v1/projects/${id}`)
