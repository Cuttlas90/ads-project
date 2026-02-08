import { defineStore } from 'pinia'

import { channelsService } from '../services/channels'
import type { ChannelStatsResponse } from '../types/api'

interface ChannelStatsState {
  stats: ChannelStatsResponse | null
  loading: boolean
  error: string | null
}

export const useChannelStatsStore = defineStore('channel-stats', {
  state: (): ChannelStatsState => ({
    stats: null,
    loading: false,
    error: null,
  }),
  getters: {
    hasPartialData: (state): boolean => {
      if (!state.stats) return false
      const hasUnavailableScalar = state.stats.scalar_metrics.some((metric) => metric.availability !== 'ready')
      const hasUnavailableChart = state.stats.chart_metrics.some((chart) => chart.availability !== 'ready')
      return hasUnavailableScalar || hasUnavailableChart
    },
    visibleCharts: (state) =>
      (state.stats?.chart_metrics ?? []).filter((chart) => chart.availability === 'ready'),
    unavailableScalars: (state) =>
      (state.stats?.scalar_metrics ?? []).filter((metric) => metric.availability !== 'ready'),
  },
  actions: {
    reset() {
      this.stats = null
      this.loading = false
      this.error = null
    },
    async fetchStats(channelId: number) {
      this.loading = true
      this.error = null
      try {
        this.stats = await channelsService.readStats(channelId)
      } catch (error) {
        this.stats = null
        this.error = error instanceof Error ? error.message : 'Failed to load channel stats'
      } finally {
        this.loading = false
      }
    },
  },
})
