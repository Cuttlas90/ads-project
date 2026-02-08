import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  listMarketplaceMock: vi.fn(),
}))

vi.mock('../services/marketplace', () => ({
  marketplaceService: {
    list: mocks.listMarketplaceMock,
  },
}))

vi.mock('../services/listings', () => ({
  listingsService: {
    create: vi.fn(),
    update: vi.fn(),
    createFormat: vi.fn(),
    updateFormat: vi.fn(),
    createDealFromListing: vi.fn(),
  },
}))

import MarketplaceView from '../views/MarketplaceView.vue'

describe('MarketplaceView structured filters and display', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listMarketplaceMock.mockResolvedValue({
      page: 1,
      page_size: 20,
      total: 1,
      items: [
        {
          listing_id: 90,
          channel_username: 'alpha',
          channel_title: 'Alpha',
          formats: [
            {
              id: 11,
              placement_type: 'story',
              exclusive_hours: 2,
              retention_hours: 24,
              price: '10.00',
            },
          ],
          stats: {
            subscribers: 1000,
            avg_views: 250,
            premium_ratio: 0.2,
          },
        },
      ],
    })
  })

  it('renders structured format commitments and forwards structured filters', async () => {
    const wrapper = mount(MarketplaceView)
    await flushPromises()

    expect(wrapper.text()).toContain('exclusive')
    expect(wrapper.text()).toContain('retention')
    expect(mocks.listMarketplaceMock).toHaveBeenCalledTimes(1)

    const placementSelect = wrapper.find('select.marketplace__select')
    await placementSelect.setValue('story')

    const numberInputs = wrapper.findAll('input[type="number"]')
    await numberInputs[0].setValue('5')
    await numberInputs[1].setValue('20')
    await numberInputs[2].setValue('2')
    await numberInputs[4].setValue('24')

    const applyButton = wrapper.findAll('button').find((button) => button.text().includes('Apply filters'))
    expect(applyButton).toBeDefined()
    await applyButton!.trigger('click')
    await flushPromises()

    expect(mocks.listMarketplaceMock).toHaveBeenLastCalledWith({
      search: undefined,
      min_price: 5,
      max_price: 20,
      placement_type: 'story',
      min_exclusive_hours: 2,
      max_exclusive_hours: undefined,
      min_retention_hours: 24,
      max_retention_hours: undefined,
    })
  })
})
