import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  readListingMock: vi.fn(),
  createListingMock: vi.fn(),
  updateListingMock: vi.fn(),
  createFormatMock: vi.fn(),
  updateFormatMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
}))

vi.mock('../services/channels', () => ({
  channelsService: {
    list: vi.fn(),
    create: vi.fn(),
    verify: vi.fn(),
    readListing: mocks.readListingMock,
  },
}))

vi.mock('../services/listings', () => ({
  listingsService: {
    create: mocks.createListingMock,
    update: mocks.updateListingMock,
    createFormat: mocks.createFormatMock,
    updateFormat: mocks.updateFormatMock,
    createDealFromListing: vi.fn(),
  },
}))

import ListingEditorView from '../views/ListingEditorView.vue'

describe('ListingEditorView structured format flows', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.readListingMock.mockResolvedValue({
      has_listing: true,
      listing: {
        id: 10,
        channel_id: 1,
        owner_id: 99,
        is_active: false,
        formats: [
          {
            id: 301,
            listing_id: 10,
            placement_type: 'post',
            exclusive_hours: 1,
            retention_hours: 24,
            price: '12.50',
          },
        ],
      },
    })
    mocks.createListingMock.mockResolvedValue({ id: 10, channel_id: 1, owner_id: 99, is_active: false })
    mocks.updateListingMock.mockResolvedValue({ id: 10, channel_id: 1, owner_id: 99, is_active: true })
    mocks.createFormatMock.mockResolvedValue({
      id: 302,
      listing_id: 10,
      placement_type: 'story',
      exclusive_hours: 2,
      retention_hours: 24,
      price: '15',
    })
    mocks.updateFormatMock.mockResolvedValue({
      id: 301,
      listing_id: 10,
      placement_type: 'story',
      exclusive_hours: 3,
      retention_hours: 36,
      price: '20',
    })
  })

  it('sends structured payloads when adding and updating formats', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const wrapper = mount(ListingEditorView, {
      global: {
        plugins: [pinia],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Exclusive hours')
    expect(wrapper.text()).toContain('Retention hours')

    const selects = wrapper.findAll('select')
    const numberInputs = wrapper.findAll('input[type="number"]')

    await selects[0].setValue('story')
    await numberInputs[0].setValue('3')
    await numberInputs[1].setValue('36')
    await numberInputs[2].setValue('20')

    const saveButton = wrapper.findAll('button').find((button) => button.text().includes('Save'))
    expect(saveButton).toBeDefined()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(mocks.updateFormatMock).toHaveBeenCalledWith(10, 301, {
      placement_type: 'story',
      exclusive_hours: 3,
      retention_hours: 36,
      price: 20,
    })

    await selects[1].setValue('story')
    await numberInputs[3].setValue('2')
    await numberInputs[4].setValue('24')
    await numberInputs[5].setValue('15')

    const addButton = wrapper.findAll('button').find((button) => button.text().includes('Add format'))
    expect(addButton).toBeDefined()
    await addButton!.trigger('click')
    await flushPromises()

    expect(mocks.createFormatMock).toHaveBeenCalledWith(10, {
      placement_type: 'story',
      exclusive_hours: 2,
      retention_hours: 24,
      price: 15,
    })
  })
})
