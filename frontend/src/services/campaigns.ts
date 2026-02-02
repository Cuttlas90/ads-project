import { api } from './api'

export const campaignsService = {
  create(payload: Record<string, unknown>) {
    return api.post('/campaigns', payload)
  },
  list(params: { page?: number; page_size?: number } = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.set(key, String(value))
      }
    })
    const suffix = query.toString()
    return api.get(`/campaigns${suffix ? `?${suffix}` : ''}`)
  },
  get(campaignId: number) {
    return api.get(`/campaigns/${campaignId}`)
  },
}
