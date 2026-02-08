import { api } from './api'
import type { ChannelListingResponse, ChannelStatsResponse, ChannelSummary } from '../types/api'

export const channelsService = {
  list() {
    return api.get<ChannelSummary[]>('/channels')
  },
  create(username: string) {
    return api.post<ChannelSummary>('/channels', { username })
  },
  verify(channelId: number) {
    return api.post<ChannelSummary>(`/channels/${channelId}/verify`)
  },
  readListing(channelId: number) {
    return api.get<ChannelListingResponse>(`/channels/${channelId}/listing`)
  },
  readStats(channelId: number) {
    return api.get<ChannelStatsResponse>(`/channels/${channelId}/stats`)
  },
}
