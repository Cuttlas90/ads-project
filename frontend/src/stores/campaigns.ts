import { defineStore } from 'pinia'

import { campaignsService } from '../services/campaigns'

interface CampaignsState {
  items: unknown[]
  loading: boolean
  error: string | null
}

export const useCampaignsStore = defineStore('campaigns', {
  state: (): CampaignsState => ({
    items: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchCampaigns() {
      this.loading = true
      this.error = null
      try {
        const response = await campaignsService.list()
        const data = response as { items?: unknown[] }
        this.items = data.items ?? []
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to load campaigns'
      } finally {
        this.loading = false
      }
    },
  },
})
