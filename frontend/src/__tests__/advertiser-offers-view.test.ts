import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  offersMock: vi.fn(),
  acceptMock: vi.fn(),
  uploadMock: vi.fn(),
  pushMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: mocks.pushMock }),
}))

vi.mock('../services/campaigns', () => ({
  campaignsService: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
    discover: vi.fn(),
    offers: mocks.offersMock,
    apply: vi.fn(),
    accept: mocks.acceptMock,
    uploadCreative: mocks.uploadMock,
    get: vi.fn(),
  },
}))

import AdvertiserOffersView from '../views/AdvertiserOffersView.vue'

describe('AdvertiserOffersView inbox and accept redirect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.offersMock.mockResolvedValue({
      page: 1,
      page_size: 20,
      total: 2,
      items: [
        {
          application_id: 52,
          campaign_id: 9,
          campaign_title: 'Newest Campaign',
          channel_id: 101,
          channel_username: 'newest',
          channel_title: 'Newest Channel',
          owner_id: 88,
          proposed_format_label: 'Post',
          proposed_placement_type: 'post',
          proposed_exclusive_hours: 1,
          proposed_retention_hours: 24,
          status: 'submitted',
          created_at: '2026-02-09T12:00:00Z',
        },
        {
          application_id: 12,
          campaign_id: 3,
          campaign_title: 'Older Campaign',
          channel_id: 99,
          channel_username: 'older',
          channel_title: 'Older Channel',
          owner_id: 77,
          proposed_format_label: 'Story',
          proposed_placement_type: 'story',
          proposed_exclusive_hours: 1,
          proposed_retention_hours: 24,
          status: 'submitted',
          created_at: '2026-02-09T10:00:00Z',
        },
      ],
    })
    mocks.acceptMock.mockResolvedValue({ id: 41 })
    mocks.uploadMock.mockResolvedValue({
      creative_media_ref: 'file-ref',
      creative_media_type: 'image',
    })
  })

  it('renders newest-first offers and redirects to deal detail after accept', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(AdvertiserOffersView, {
      global: {
        plugins: [pinia],
        stubs: {
          teleport: true,
        },
      },
    })

    await flushPromises()

    const titles = wrapper
      .findAll('.offers__list .tg-card__header h3')
      .map((node) => node.text().trim())
    expect(titles).toEqual(['Newest Campaign', 'Older Campaign'])

    const acceptButton = wrapper
      .findAll('button')
      .find((button) => button.text().trim() === 'Accept + create deal')
    expect(acceptButton).toBeDefined()
    await acceptButton!.trigger('click')
    await flushPromises()

    await wrapper.find('textarea.offer__textarea').setValue('Draft text')
    await wrapper.find('select.offers__select').setValue('video')

    const file = new File(['img'], 'creative.jpg', { type: 'image/jpeg' })
    const fileInput = wrapper.find('input[type="file"]')
    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await fileInput.trigger('change')
    await flushPromises()
    await flushPromises()

    expect(mocks.uploadMock).toHaveBeenCalledTimes(1)
    expect(mocks.uploadMock).toHaveBeenCalledWith(9, 52, file)

    const createDealButton = wrapper
      .findAll('button')
      .find((button) => button.text().trim() === 'Create draft deal')
    expect(createDealButton).toBeDefined()
    await createDealButton!.trigger('click')
    await flushPromises()

    expect(mocks.acceptMock).toHaveBeenCalledWith(9, 52, {
      creative_text: 'Draft text',
      start_at: undefined,
      creative_media_type: 'image',
      creative_media_ref: 'file-ref',
    })
    expect(mocks.pushMock).toHaveBeenCalledWith('/deals/41')
  })

  it('keeps accept-modal failures in modal scope', async () => {
    mocks.acceptMock.mockRejectedValueOnce(new Error('Accept failed in modal'))

    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(AdvertiserOffersView, {
      global: {
        plugins: [pinia],
        stubs: {
          teleport: true,
        },
      },
    })

    await flushPromises()

    const acceptButton = wrapper
      .findAll('button')
      .find((button) => button.text().trim() === 'Accept + create deal')
    await acceptButton!.trigger('click')
    await flushPromises()

    await wrapper.find('textarea.offer__textarea').setValue('Draft text')

    const file = new File(['img'], 'creative.jpg', { type: 'image/jpeg' })
    const fileInput = wrapper.find('input[type="file"]')
    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await fileInput.trigger('change')
    await flushPromises()

    const createDealButton = wrapper
      .findAll('button')
      .find((button) => button.text().trim() === 'Create draft deal')
    await createDealButton!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.tg-modal__body').text()).toContain('Accept failed in modal')
    expect(wrapper.text()).not.toContain("Couldn't load offers")
  })
})
