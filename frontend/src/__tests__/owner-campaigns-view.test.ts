import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  discoverMock: vi.fn(),
  applyMock: vi.fn(),
  listChannelsMock: vi.fn(),
}))

vi.mock('../services/campaigns', () => ({
  campaignsService: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
    discover: mocks.discoverMock,
    offers: vi.fn(),
    apply: mocks.applyMock,
    accept: vi.fn(),
    get: vi.fn(),
  },
}))

vi.mock('../services/channels', () => ({
  channelsService: {
    list: mocks.listChannelsMock,
    create: vi.fn(),
    verify: vi.fn(),
    readListing: vi.fn(),
  },
}))

import OwnerCampaignsView from '../views/OwnerCampaignsView.vue'

describe('OwnerCampaignsView apply channel picker', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.discoverMock.mockResolvedValue({
      page: 1,
      page_size: 20,
      total: 1,
      items: [
        {
          id: 77,
          advertiser_id: 11,
          title: 'Summer',
          brief: 'Need post',
          budget_ton: '10.00',
          preferred_language: null,
          min_subscribers: null,
          min_avg_views: null,
          max_acceptances: 10,
          created_at: '2026-02-09T00:00:00Z',
          updated_at: '2026-02-09T00:00:00Z',
        },
      ],
    })
    mocks.listChannelsMock.mockResolvedValue([
      { id: 10, username: 'channel_a', title: 'Channel A', is_verified: true, role: 'owner' },
      { id: 20, username: 'channel_b', title: 'Channel B', is_verified: true, role: 'owner' },
    ])
    mocks.applyMock.mockResolvedValue({
      id: 1,
      campaign_id: 77,
      channel_id: 10,
      owner_id: 33,
      proposed_format_label: 'Post',
      proposed_placement_type: 'post',
      proposed_exclusive_hours: 1,
      proposed_retention_hours: 24,
      message: null,
      status: 'submitted',
      created_at: '2026-02-09T00:00:00Z',
    })
  })

  it('allows applying to same campaign from multiple owned verified channels', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(OwnerCampaignsView, {
      global: {
        plugins: [pinia],
      },
    })

    await flushPromises()

    const channelSelect = wrapper.find('select.owner-campaigns__select')
    await channelSelect.setValue('10')

    const applyButton = wrapper.findAll('button').find((button) => button.text().trim() === 'Apply')
    expect(applyButton).toBeDefined()
    await applyButton!.trigger('click')
    await flushPromises()

    await channelSelect.setValue('20')
    await applyButton!.trigger('click')
    await flushPromises()

    expect(mocks.applyMock).toHaveBeenCalledTimes(2)
    expect(mocks.applyMock).toHaveBeenNthCalledWith(
      1,
      77,
      expect.objectContaining({
        channel_id: 10,
        proposed_format_label: 'Post',
        proposed_placement_type: 'post',
        proposed_exclusive_hours: 0,
        proposed_retention_hours: 24,
      }),
    )
    expect(mocks.applyMock).toHaveBeenNthCalledWith(
      2,
      77,
      expect.objectContaining({
        channel_id: 20,
        proposed_format_label: 'Post',
        proposed_placement_type: 'post',
        proposed_exclusive_hours: 0,
        proposed_retention_hours: 24,
      }),
    )
  })
})
