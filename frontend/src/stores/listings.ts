import { defineStore } from 'pinia'

import type { ListingDetail, ListingFormatSummary } from '../types/api'
import type { ListingFormatPayload, ListingFormatUpdatePayload } from '../services/listings'
import { listingsService } from '../services/listings'

interface ListingsState {
  listing: ListingDetail | null
  loading: boolean
  error: string | null
}

export const useListingsStore = defineStore('listings', {
  state: (): ListingsState => ({
    listing: null,
    loading: false,
    error: null,
  }),
  actions: {
    setListing(listing: ListingDetail | null) {
      this.listing = listing
    },
    async createListing(channelId: number) {
      this.loading = true
      this.error = null
      try {
        const summary = await listingsService.create(channelId)
        this.listing = { ...summary, formats: [] }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to create listing'
      } finally {
        this.loading = false
      }
    },
    async updateListing(isActive: boolean) {
      if (!this.listing) return
      this.loading = true
      this.error = null
      try {
        const summary = await listingsService.update(this.listing.id, isActive)
        this.listing = { ...summary, formats: this.listing.formats }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to update listing'
      } finally {
        this.loading = false
      }
    },
    async addFormat(payload: ListingFormatPayload) {
      if (!this.listing) return
      this.loading = true
      this.error = null
      try {
        const format = await listingsService.createFormat(this.listing.id, payload)
        this.listing = {
          ...this.listing,
          formats: [...this.listing.formats, format],
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to add format'
      } finally {
        this.loading = false
      }
    },
    async updateFormat(format: ListingFormatSummary, payload: ListingFormatUpdatePayload) {
      if (!this.listing) return
      this.loading = true
      this.error = null
      try {
        const updated = await listingsService.updateFormat(this.listing.id, format.id, payload)
        this.listing = {
          ...this.listing,
          formats: this.listing.formats.map((item) => (item.id === updated.id ? updated : item)),
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to update format'
      } finally {
        this.loading = false
      }
    },
  },
})
