import { api } from './api'
import type { MarketplaceListingPage } from '../types/api'

export interface MarketplaceQuery {
  min_price?: number
  max_price?: number
  min_subscribers?: number
  max_subscribers?: number
  min_avg_views?: number
  max_avg_views?: number
  language?: string
  min_premium_pct?: number
  search?: string
  page?: number
  page_size?: number
  sort?: 'price' | 'subscribers'
}

export const marketplaceService = {
  list(params: MarketplaceQuery = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.set(key, String(value))
      }
    })
    const suffix = query.toString()
    return api.get<MarketplaceListingPage>(`/marketplace/listings${suffix ? `?${suffix}` : ''}`)
  },
}
