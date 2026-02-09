import { api } from './api'
import type { DealDetail, DealInboxPage, DealTimelinePage } from '../types/api'

export const dealsService = {
  list(
    params: {
      role?: 'owner' | 'advertiser'
      state?: string
      page?: number
      page_size?: number
    } = {},
  ) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.set(key, String(value))
      }
    })
    const suffix = query.toString()
    return api.get<DealInboxPage>(`/deals${suffix ? `?${suffix}` : ''}`)
  },
  get(dealId: number) {
    return api.get<DealDetail>(`/deals/${dealId}`)
  },
  events(dealId: number, params: { cursor?: string; limit?: number } = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.set(key, String(value))
      }
    })
    const suffix = query.toString()
    return api.get<DealTimelinePage>(`/deals/${dealId}/events${suffix ? `?${suffix}` : ''}`)
  },
  update(
    dealId: number,
    payload: {
      creative_text?: string
      start_at?: string | null
      creative_media_type?: string
      creative_media_ref?: string
    },
  ) {
    return api.patch(`/deals/${dealId}`, payload)
  },
  accept(dealId: number) {
    return api.post(`/deals/${dealId}/accept`)
  },
  reject(dealId: number) {
    return api.post(`/deals/${dealId}/reject`)
  },
  submitCreative(
    dealId: number,
    payload: { creative_text: string; creative_media_type: string; creative_media_ref: string },
  ) {
    return api.post(`/deals/${dealId}/creative/submit`, payload)
  },
  approveCreative(dealId: number) {
    return api.post(`/deals/${dealId}/creative/approve`)
  },
  requestEdits(dealId: number) {
    return api.post(`/deals/${dealId}/creative/request-edits`)
  },
  uploadCreative(dealId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{ creative_media_ref: string; creative_media_type: string }>(
      `/deals/${dealId}/creative/upload`,
      formData,
    )
  },
  uploadProposalMedia(dealId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{ creative_media_ref: string; creative_media_type: string }>(
      `/deals/${dealId}/proposal/upload`,
      formData,
    )
  },
  escrowInit(dealId: number) {
    return api.post(`/deals/${dealId}/escrow/init`)
  },
  tonconnectTx(dealId: number) {
    return api.post(`/deals/${dealId}/escrow/tonconnect-tx`)
  },
  escrowStatus(dealId: number) {
    return api.get(`/deals/${dealId}/escrow`)
  },
}
