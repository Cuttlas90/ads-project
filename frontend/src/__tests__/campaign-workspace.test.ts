import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  listMock: vi.fn(),
  createMock: vi.fn(),
  deleteMock: vi.fn(),
  discoverMock: vi.fn(),
  offersMock: vi.fn(),
  applyMock: vi.fn(),
  acceptMock: vi.fn(),
  getMock: vi.fn(),
}))

vi.mock('../services/campaigns', () => ({
  campaignsService: {
    list: mocks.listMock,
    create: mocks.createMock,
    delete: mocks.deleteMock,
    discover: mocks.discoverMock,
    offers: mocks.offersMock,
    apply: mocks.applyMock,
    accept: mocks.acceptMock,
    get: mocks.getMock,
  },
}))

import CampaignCreateView from '../views/CampaignCreateView.vue'

const campaignSummary = (overrides: Record<string, unknown> = {}) => ({
  id: 1,
  advertiser_id: 10,
  title: 'Existing Campaign',
  brief: 'Existing brief',
  budget_usdt: null,
  budget_ton: '20.00',
  preferred_language: null,
  start_at: null,
  end_at: null,
  min_subscribers: null,
  min_avg_views: null,
  lifecycle_state: 'active',
  max_acceptances: 10,
  hidden_at: null,
  is_active: true,
  created_at: '2026-02-09T00:00:00Z',
  updated_at: '2026-02-09T00:00:00Z',
  ...overrides,
})

describe('CampaignCreateView workspace flows', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listMock.mockResolvedValue({
      page: 1,
      page_size: 20,
      total: 1,
      items: [campaignSummary()],
    })
    mocks.createMock.mockResolvedValue(campaignSummary({ id: 2, title: 'Created Campaign' }))
    mocks.deleteMock.mockResolvedValue(undefined)
    mocks.discoverMock.mockResolvedValue({ page: 1, page_size: 20, total: 0, items: [] })
    mocks.offersMock.mockResolvedValue({ page: 1, page_size: 20, total: 0, items: [] })
    mocks.applyMock.mockResolvedValue({})
    mocks.acceptMock.mockResolvedValue({ id: 88 })
    mocks.getMock.mockResolvedValue(campaignSummary())
  })

  it('renders advertiser campaigns below form and appends created campaign', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(CampaignCreateView, {
      global: {
        plugins: [pinia],
        stubs: {
          teleport: true,
          RouterLink: {
            props: ['to'],
            template: '<a><slot /></a>',
          },
        },
      },
    })

    await flushPromises()
    expect(wrapper.text()).toContain('Existing Campaign')

    await wrapper.find('input[placeholder="Spring launch"]').setValue('Created Campaign')
    await wrapper.find('input[placeholder="What should owners know?"]').setValue('Created brief')
    const numberInputs = wrapper.findAll('input[type="number"]')
    await numberInputs[0].setValue('15')

    const createButton = wrapper.findAll('button').find((button) => button.text().includes('Create campaign'))
    expect(createButton).toBeDefined()
    await createButton!.trigger('click')
    await flushPromises()

    expect(mocks.createMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Created Campaign')
  })

  it('keeps delete label and explains hidden semantics before removing campaign', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(CampaignCreateView, {
      global: {
        plugins: [pinia],
        stubs: {
          teleport: true,
          RouterLink: {
            props: ['to'],
            template: '<a><slot /></a>',
          },
        },
      },
    })

    await flushPromises()
    expect(wrapper.text()).toContain('Existing Campaign')

    const rowDeleteButton = wrapper.findAll('button').find((button) => button.text().trim() === 'Delete campaign')
    expect(rowDeleteButton).toBeDefined()
    await rowDeleteButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('related offers from campaign pages')

    const modalDeleteButtons = wrapper
      .findAll('button')
      .filter((button) => button.text().trim() === 'Delete campaign')
    await modalDeleteButtons[modalDeleteButtons.length - 1].trigger('click')
    await flushPromises()

    expect(mocks.deleteMock).toHaveBeenCalledWith(1)
    expect(wrapper.text()).not.toContain('Existing Campaign')
  })
})
