import { RouterLinkStub, flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  listMarketplaceMock: vi.fn(),
  createDealFromListingMock: vi.fn(),
  uploadCreativeMock: vi.fn(),
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
    createDealFromListing: mocks.createDealFromListingMock,
    uploadCreative: mocks.uploadCreativeMock,
  },
}))

import MarketplaceView from '../views/MarketplaceView.vue'

describe('MarketplaceView structured filters and display', () => {
  const mountView = () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    return mount(MarketplaceView, {
      global: {
        plugins: [pinia],
        stubs: {
          teleport: true,
          RouterLink: RouterLinkStub,
        },
      },
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mocks.createDealFromListingMock.mockResolvedValue({ id: 1 })
    mocks.uploadCreativeMock.mockResolvedValue({
      creative_media_ref: 'file-123',
      creative_media_type: 'image',
    })
    mocks.listMarketplaceMock.mockResolvedValue({
      page: 1,
      page_size: 20,
      total: 1,
      items: [
        {
          listing_id: 90,
          channel_id: 12,
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
    const wrapper = mountView()
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

  it('enforces upload-first start deal and submits using upload response media fields', async () => {
    const wrapper = mountView()
    await flushPromises()

    const formatButton = wrapper.findAll('button').find((button) => button.text().includes('exclusive'))
    expect(formatButton).toBeDefined()
    await formatButton!.trigger('click')
    await flushPromises()

    let startButton = wrapper.find('.tg-modal__footer .tg-button')
    expect(startButton.exists()).toBe(true)
    expect(startButton.attributes('disabled')).toBeDefined()

    await wrapper.find('textarea.marketplace__textarea').setValue('Launch copy')
    startButton = wrapper.find('.tg-modal__footer .tg-button')
    expect(startButton.attributes('disabled')).toBeDefined()

    const modalSelects = wrapper.findAll('select.marketplace__select')
    await modalSelects[1].setValue('video')

    const file = new File(['img'], 'creative.jpg', { type: 'image/jpeg' })
    const fileInput = wrapper.find('input[type="file"]')
    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await fileInput.trigger('change')
    await flushPromises()
    await flushPromises()

    expect(mocks.uploadCreativeMock).toHaveBeenCalledTimes(1)
    expect(mocks.uploadCreativeMock).toHaveBeenCalledWith(90, file)
    startButton = wrapper.find('.tg-modal__footer .tg-button')
    expect(startButton.attributes('disabled')).toBeUndefined()

    await startButton.trigger('click')
    await flushPromises()

    expect(mocks.createDealFromListingMock).toHaveBeenCalledTimes(1)
    expect(mocks.createDealFromListingMock).toHaveBeenCalledWith(90, {
      listing_format_id: 11,
      creative_text: 'Launch copy',
      start_at: undefined,
      creative_media_type: 'image',
      creative_media_ref: 'file-123',
    })
  })

  it('keeps modal-origin upload errors in modal scope', async () => {
    mocks.uploadCreativeMock.mockRejectedValueOnce(new Error('Upload failed in modal'))
    const wrapper = mountView()
    await flushPromises()

    const formatButton = wrapper.findAll('button').find((button) => button.text().includes('exclusive'))
    await formatButton!.trigger('click')
    await flushPromises()

    const file = new File(['img'], 'creative.jpg', { type: 'image/jpeg' })
    const fileInput = wrapper.find('input[type="file"]')
    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await fileInput.trigger('change')
    await flushPromises()

    expect(wrapper.find('.tg-modal__body').text()).toContain('Upload failed in modal')
    expect(wrapper.text()).not.toContain("Couldn't load listings")
  })
})
