import { defineStore } from 'pinia'

import type { DealInboxPage } from '../types/api'
import { dealsService } from '../services/deals'

interface DealsState {
  inbox: DealInboxPage | null
  loading: boolean
  error: string | null
}

export const useDealsStore = defineStore('deals', {
  state: (): DealsState => ({
    inbox: null,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchInbox(
      params: { role?: 'owner' | 'advertiser'; state?: string; page?: number } = {},
    ) {
      this.loading = true
      this.error = null
      try {
        this.inbox = await dealsService.list(params)
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to load deals'
      } finally {
        this.loading = false
      }
    },
  },
})
