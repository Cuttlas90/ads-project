import { api } from './api'
import type { ListingFormatSummary, ListingSummary } from '../types/api'

export const listingsService = {
  create(channel_id: number) {
    return api.post<ListingSummary>('/listings', { channel_id })
  },
  update(listingId: number, is_active: boolean) {
    return api.put<ListingSummary>(`/listings/${listingId}`, { is_active })
  },
  createFormat(listingId: number, label: string, price: number) {
    return api.post<ListingFormatSummary>(`/listings/${listingId}/formats`, { label, price })
  },
  updateFormat(listingId: number, formatId: number, payload: { label?: string; price?: number }) {
    return api.put<ListingFormatSummary>(`/listings/${listingId}/formats/${formatId}`, payload)
  },
  createDealFromListing(listingId: number, payload: Record<string, unknown>) {
    return api.post(`/listings/${listingId}/deals`, payload)
  },
}
