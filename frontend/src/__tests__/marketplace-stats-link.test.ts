import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import MarketplaceView from '../views/MarketplaceView.vue'
import { marketplaceService } from '../services/marketplace'

vi.mock('../services/listings', () => ({
  listingsService: {
    createDealFromListing: vi.fn(),
  },
}))

describe('Marketplace stats navigation', () => {
  it('renders channel name/title as a stats link using channel_id', async () => {
    vi.spyOn(marketplaceService, 'list').mockResolvedValueOnce({
      page: 1,
      page_size: 20,
      total: 1,
      items: [
        {
          listing_id: 11,
          channel_id: 42,
          channel_username: 'alpha_channel',
          channel_title: 'Alpha Channel',
          formats: [{ id: 1, format_id: 1, label: 'Post', price: '12.00' }],
          stats: { subscribers: 1200, avg_views: 600, premium_ratio: 0.12 },
        },
      ],
    })

    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/advertiser/marketplace', component: MarketplaceView },
        { path: '/advertiser/channels/:channelId/stats', component: { template: '<div>stats</div>' } },
      ],
    })
    await router.push('/advertiser/marketplace')
    await router.isReady()

    const wrapper = mount(MarketplaceView, {
      global: {
        plugins: [pinia, router],
      },
    })
    await flushPromises()

    const statsLink = wrapper.find('.marketplace__channel-link')
    expect(statsLink.exists()).toBe(true)
    expect(statsLink.attributes('href')).toContain('/advertiser/channels/42/stats')
    expect(statsLink.text()).toContain('Alpha Channel')
  })
})
