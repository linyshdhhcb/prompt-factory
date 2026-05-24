import api from './index'

export interface PersonaTraitCreate {
  category: string
  label: string
  traits?: any[]
  weight?: number
  scope?: 'public' | 'project'
  project_id?: string | null
}

export interface PersonaTraitUpdate {
  category?: string
  label?: string
  traits?: any[]
  weight?: number
  scope?: 'public' | 'project'
  project_id?: string | null
}

export interface PersonaTraitResponse {
  id: number
  category: string
  label: string
  traits: any[]
  weight: number
  scope: string
  project_id: string | null
  created_at: string
  updated_at: string
}

export interface PersonaTraitListResponse {
  items: PersonaTraitResponse[]
  total: number
}

export const listTraits = (params?: { offset?: number; limit?: number; category?: string; scope?: string; project_id?: string }) =>
  api.get<PersonaTraitListResponse>('/api/v1/persona/traits', { params })

export const createTrait = (data: PersonaTraitCreate) =>
  api.post<PersonaTraitResponse>('/api/v1/persona/traits', data)

export const updateTrait = (id: number, data: PersonaTraitUpdate) =>
  api.put<PersonaTraitResponse>(`/api/v1/persona/traits/${id}`, data)

export const deleteTrait = (id: number) =>
  api.delete(`/api/v1/persona/traits/${id}`)

export const importTraits = (formData: FormData) =>
  api.post('/api/v1/persona/traits/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const previewPersona = (projectId: string) =>
  api.get(`/api/v1/persona/preview/${projectId}`)
