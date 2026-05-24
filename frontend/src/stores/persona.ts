import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  listTraits,
  createTrait,
  updateTrait,
  deleteTrait,
  importTraits,
  previewPersona,
  type PersonaTraitResponse,
  type PersonaTraitCreate,
  type PersonaTraitUpdate,
} from '@/api/persona'

export const usePersonaStore = defineStore('persona', () => {
  const traits = ref<PersonaTraitResponse[]>([])
  const total = ref(0)
  const loading = ref(false)
  const personaPreview = ref<Record<string, any> | null>(null)

  const fetchTraits = async (params?: { offset?: number; limit?: number; category?: string; scope?: string; project_id?: string }) => {
    loading.value = true
    try {
      const { data } = await listTraits(params)
      traits.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  const addTrait = async (payload: PersonaTraitCreate) => {
    const { data } = await createTrait(payload)
    traits.value.unshift(data)
    total.value += 1
    return data
  }

  const editTrait = async (id: number, payload: PersonaTraitUpdate) => {
    const { data } = await updateTrait(id, payload)
    const idx = traits.value.findIndex((t) => t.id === id)
    if (idx !== -1) traits.value[idx] = data
    return data
  }

  const removeTrait = async (id: number) => {
    await deleteTrait(id)
    traits.value = traits.value.filter((t) => t.id !== id)
    total.value -= 1
  }

  const importFromFile = async (formData: FormData) => {
    const { data } = await importTraits(formData)
    return data
  }

  const fetchPreview = async (projectId: string) => {
    const { data } = await previewPersona(projectId)
    personaPreview.value = data
    return data
  }

  return {
    traits,
    total,
    loading,
    personaPreview,
    fetchTraits,
    addTrait,
    editTrait,
    removeTrait,
    importFromFile,
    fetchPreview,
  }
})
