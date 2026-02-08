import { api } from './api'
import type { ListingFormatSummary, ListingSummary } from '../types/api'

export interface ListingFormatPayload {
  placement_type: 'post' | 'story'
  exclusive_hours: number
  retention_hours: number
  price: number
}

export interface ListingFormatUpdatePayload {
  placement_type?: 'post' | 'story'
  exclusive_hours?: number
  retention_hours?: number
  price?: number
}

export const listingsService = {
  create(channel_id: number) {
    return api.post<ListingSummary>('/listings', { channel_id })
  },
  update(listingId: number, is_active: boolean) {
    return api.put<ListingSummary>(`/listings/${listingId}`, { is_active })
  },
  createFormat(listingId: number, payload: ListingFormatPayload) {
    return api.post<ListingFormatSummary>(`/listings/${listingId}/formats`, payload)
  },
  updateFormat(listingId: number, formatId: number, payload: ListingFormatUpdatePayload) {
    return api.put<ListingFormatSummary>(`/listings/${listingId}/formats/${formatId}`, payload)
  },
  createDealFromListing(listingId: number, payload: Record<string, unknown>) {
    return api.post(`/listings/${listingId}/deals`, payload)
  },
}
