import { defineStore } from 'pinia'

import type {
  CampaignApplicationSummary,
  CampaignDiscoverPage,
  CampaignOfferInboxPage,
  CampaignPage,
  CampaignSummary,
} from '../types/api'
import { campaignsService } from '../services/campaigns'

interface CampaignsState {
  advertiserPage: CampaignPage | null
  discoverPage: CampaignDiscoverPage | null
  offersPage: CampaignOfferInboxPage | null
  loadingAdvertiser: boolean
  loadingDiscover: boolean
  loadingOffers: boolean
  creating: boolean
  deleting: boolean
  applying: boolean
  accepting: boolean
  error: string | null
}

export const useCampaignsStore = defineStore('campaigns', {
  state: (): CampaignsState => ({
    advertiserPage: null,
    discoverPage: null,
    offersPage: null,
    loadingAdvertiser: false,
    loadingDiscover: false,
    loadingOffers: false,
    creating: false,
    deleting: false,
    applying: false,
    accepting: false,
    error: null,
  }),
  actions: {
    clearError() {
      this.error = null
    },
    async fetchAdvertiserCampaigns(params: { page?: number; page_size?: number } = {}) {
      this.loadingAdvertiser = true
      this.error = null
      try {
        this.advertiserPage = await campaignsService.list(params)
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to load campaigns'
      } finally {
        this.loadingAdvertiser = false
      }
    },
    async fetchDiscoverCampaigns(
      params: { page?: number; page_size?: number; search?: string } = {},
    ) {
      this.loadingDiscover = true
      this.error = null
      try {
        this.discoverPage = await campaignsService.discover(params)
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to load discover campaigns'
      } finally {
        this.loadingDiscover = false
      }
    },
    async fetchOffers(params: { page?: number; page_size?: number } = {}) {
      this.loadingOffers = true
      this.error = null
      try {
        this.offersPage = await campaignsService.offers(params)
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to load offers'
      } finally {
        this.loadingOffers = false
      }
    },
    async createCampaign(payload: Record<string, unknown>): Promise<CampaignSummary> {
      this.creating = true
      this.error = null
      try {
        const created = await campaignsService.create(payload)
        if (this.advertiserPage) {
          this.advertiserPage = {
            ...this.advertiserPage,
            total: this.advertiserPage.total + 1,
            items: [created, ...this.advertiserPage.items],
          }
        }
        return created
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to create campaign'
        throw error
      } finally {
        this.creating = false
      }
    },
    async deleteCampaign(campaignId: number): Promise<void> {
      this.deleting = true
      this.error = null
      try {
        await campaignsService.delete(campaignId)
        if (this.advertiserPage) {
          const nextItems = this.advertiserPage.items.filter((item) => item.id !== campaignId)
          this.advertiserPage = {
            ...this.advertiserPage,
            total: Math.max(0, this.advertiserPage.total - (this.advertiserPage.items.length - nextItems.length)),
            items: nextItems,
          }
        }
        if (this.offersPage) {
          const nextItems = this.offersPage.items.filter((item) => item.campaign_id !== campaignId)
          this.offersPage = {
            ...this.offersPage,
            total: Math.max(0, this.offersPage.total - (this.offersPage.items.length - nextItems.length)),
            items: nextItems,
          }
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to delete campaign'
        throw error
      } finally {
        this.deleting = false
      }
    },
    async applyToCampaign(
      campaignId: number,
      payload: {
        channel_id: number
        proposed_format_label?: string
        proposed_placement_type: 'post' | 'story'
        proposed_exclusive_hours: number
        proposed_retention_hours: number
        message?: string
      },
    ): Promise<CampaignApplicationSummary> {
      this.applying = true
      this.error = null
      try {
        return await campaignsService.apply(campaignId, payload)
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to apply to campaign'
        throw error
      } finally {
        this.applying = false
      }
    },
    async acceptOffer(
      campaignId: number,
      applicationId: number,
      payload: {
        creative_text: string
        creative_media_type: string
        creative_media_ref: string
        start_at?: string
      },
    ): Promise<{ id: number }> {
      this.accepting = true
      this.error = null
      try {
        return await campaignsService.accept(campaignId, applicationId, payload)
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to accept offer'
        throw error
      } finally {
        this.accepting = false
      }
    },
  },
})
