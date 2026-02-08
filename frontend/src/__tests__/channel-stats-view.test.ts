import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import { channelsService } from '../services/channels'
import { useAuthStore } from '../stores/auth'
import ChannelStatsView from '../views/ChannelStatsView.vue'

describe('ChannelStatsView', () => {
  it('hides unavailable chart sections and shows placeholders for unavailable scalar metrics', async () => {
    vi.spyOn(channelsService, 'readStats').mockResolvedValueOnce({
      channel_id: 3,
      channel_username: 'big_channel',
      channel_title: 'Big Channel',
      captured_at: '2026-02-08T00:00:00Z',
      snapshot_available: true,
      read_only: true,
      scalar_metrics: [
        { key: 'subscribers', availability: 'ready', value: 4511 },
        { key: 'avg_views', availability: 'ready', value: 1740 },
        { key: 'joins_per_post', availability: 'missing', reason: 'No data available in this snapshot.' },
      ],
      chart_metrics: [
        {
          key: 'growth_graph',
          availability: 'ready',
          data: {
            _: 'DataJSON',
            data: JSON.stringify({
              columns: [
                ['x', 1762560000000, 1762646400000, 1762732800000],
                ['y0', 1, 3, 2],
              ],
              types: { x: 'x', y0: 'line' },
              names: { y0: 'Joined' },
              colors: { y0: 'GREEN#34C759' },
            }),
          },
        },
        { key: 'premium_graph', availability: 'error', reason: 'Not enough data' },
        { key: 'interactions_graph', availability: 'async_pending', token: 'abc-token' },
        { key: 'shares_graph', availability: 'missing' },
      ],
      premium_audience: {
        availability: 'ready',
        premium_ratio: 56 / 4511,
        part: 56,
        total: 4511,
      },
    })

    const pinia = createPinia()
    setActivePinia(pinia)
    const authStore = useAuthStore()
    authStore.bootstrapped = true
    authStore.user = {
      id: 1,
      telegram_user_id: 10,
      preferred_role: 'advertiser',
      ton_wallet_address: null,
      has_wallet: false,
    }

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/advertiser/channels/:channelId/stats', component: ChannelStatsView },
        { path: '/advertiser/marketplace', component: { template: '<div>marketplace</div>' } },
      ],
    })
    await router.push('/advertiser/channels/3/stats')
    await router.isReady()

    const wrapper = mount(ChannelStatsView, {
      global: {
        plugins: [pinia, router],
      },
    })
    await flushPromises()

    const chartTitles = wrapper.findAll('.stats__chart-title').map((item) => item.text())
    expect(chartTitles).toEqual(['growth_graph'])
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.findAll('polyline')).toHaveLength(1)
    expect(wrapper.text()).toContain('Joined')
    expect(wrapper.text()).toContain('joins_per_post')
    expect(wrapper.text()).not.toContain('premium_graph')
    expect(wrapper.text()).not.toContain('interactions_graph')
    expect(wrapper.text()).not.toContain('shares_graph')
  })
})
