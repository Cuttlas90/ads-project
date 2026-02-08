import { api } from './api'
import type {
  CampaignApplicationSummary,
  CampaignDiscoverPage,
  CampaignOfferInboxPage,
  CampaignPage,
  CampaignSummary,
} from '../types/api'

export const campaignsService = {
  create(payload: Record<string, unknown>) {
    return api.post<CampaignSummary>('/campaigns', payload)
  },
  list(params: { page?: number; page_size?: number } = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.set(key, String(value))
      }
    })
    const suffix = query.toString()
    return api.get<CampaignPage>(`/campaigns${suffix ? `?${suffix}` : ''}`)
  },
  discover(params: { page?: number; page_size?: number; search?: string } = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && String(value).trim() !== '') {
        query.set(key, String(value))
      }
    })
    const suffix = query.toString()
    return api.get<CampaignDiscoverPage>(`/campaigns/discover${suffix ? `?${suffix}` : ''}`)
  },
  offers(params: { page?: number; page_size?: number } = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.set(key, String(value))
      }
    })
    const suffix = query.toString()
    return api.get<CampaignOfferInboxPage>(`/campaigns/offers${suffix ? `?${suffix}` : ''}`)
  },
  get(campaignId: number) {
    return api.get<CampaignSummary>(`/campaigns/${campaignId}`)
  },
  delete(campaignId: number) {
    return api.delete<void>(`/campaigns/${campaignId}`)
  },
  apply(
    campaignId: number,
    payload: {
      channel_id: number
      proposed_format_label: string
      message?: string
    },
  ) {
    return api.post<CampaignApplicationSummary>(`/campaigns/${campaignId}/apply`, payload)
  },
  accept(
    campaignId: number,
    applicationId: number,
    payload: {
      price_ton: string
      ad_type: string
      creative_text: string
      creative_media_type: string
      creative_media_ref: string
    },
  ) {
    return api.post<{ id: number }>(
      `/campaigns/${campaignId}/applications/${applicationId}/accept`,
      payload,
    )
  },
}
