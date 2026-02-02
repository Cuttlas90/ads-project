import { defineStore } from 'pinia'

import type { ChannelListingResponse, ChannelSummary } from '../types/api'
import { channelsService } from '../services/channels'

interface ChannelsState {
  items: ChannelSummary[]
  listing: ChannelListingResponse | null
  loading: boolean
  error: string | null
}

export const useChannelsStore = defineStore('channels', {
  state: (): ChannelsState => ({
    items: [],
    listing: null,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchChannels() {
      this.loading = true
      this.error = null
      try {
        this.items = await channelsService.list()
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to load channels'
      } finally {
        this.loading = false
      }
    },
    async addChannel(username: string) {
      this.loading = true
      this.error = null
      try {
        const channel = await channelsService.create(username)
        this.items = [...this.items, channel]
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to add channel'
      } finally {
        this.loading = false
      }
    },
    async verifyChannel(channelId: number) {
      this.loading = true
      this.error = null
      try {
        const channel = await channelsService.verify(channelId)
        this.items = this.items.map((item) => (item.id === channel.id ? channel : item))
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to verify channel'
      } finally {
        this.loading = false
      }
    },
    async fetchListing(channelId: number) {
      this.loading = true
      this.error = null
      try {
        this.listing = await channelsService.readListing(channelId)
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to load listing'
      } finally {
        this.loading = false
      }
    },
  },
})
