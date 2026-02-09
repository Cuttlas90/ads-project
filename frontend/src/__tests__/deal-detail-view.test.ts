import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  getMock: vi.fn(),
  eventsMock: vi.fn(),
  updateMock: vi.fn(),
  acceptMock: vi.fn(),
  rejectMock: vi.fn(),
  uploadProposalMediaMock: vi.fn(),
  pushMock: vi.fn(),
  replaceMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '77' }, query: {} }),
  useRouter: () => ({ push: mocks.pushMock, replace: mocks.replaceMock }),
}))

vi.mock('../services/deals', () => ({
  dealsService: {
    list: vi.fn(),
    get: mocks.getMock,
    events: mocks.eventsMock,
    update: mocks.updateMock,
    accept: mocks.acceptMock,
    reject: mocks.rejectMock,
    uploadProposalMedia: mocks.uploadProposalMediaMock,
    submitCreative: vi.fn(),
    approveCreative: vi.fn(),
    requestEdits: vi.fn(),
    uploadCreative: vi.fn(),
    escrowInit: vi.fn(),
    tonconnectTx: vi.fn(),
    escrowStatus: vi.fn(),
  },
}))

import DealDetailView from '../views/DealDetailView.vue'
import { useAuthStore } from '../stores/auth'

const baseDeal = {
  id: 77,
  source_type: 'listing',
  advertiser_id: 101,
  channel_id: 31,
  channel_owner_id: 202,
  listing_id: 5,
  listing_format_id: 8,
  campaign_id: null,
  campaign_application_id: null,
  price_ton: '10.00',
  ad_type: 'post',
  placement_type: 'post',
  exclusive_hours: 1,
  retention_hours: 24,
  creative_text: 'Original text',
  creative_media_type: 'image',
  creative_media_ref: 'ref-1',
  posting_params: { hour: 10 },
  scheduled_at: '2026-02-10T10:00:00Z',
  verification_window_hours: 24,
  posted_at: null,
  posted_message_id: null,
  posted_content_hash: null,
  verified_at: null,
  state: 'DRAFT',
  created_at: '2026-02-09T00:00:00Z',
  updated_at: '2026-02-09T00:00:00Z',
  channel_username: 'channel',
  channel_title: 'Channel title',
  advertiser_username: 'adv',
  advertiser_first_name: 'Ada',
  advertiser_last_name: 'Lovelace',
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const expectedTimelineFormat = (date: Date) => {
  const now = new Date()
  const sameYear = date.getFullYear() === now.getFullYear()
  const sameDay =
    sameYear && date.getMonth() === now.getMonth() && date.getDate() === now.getDate()

  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const month = MONTHS[date.getMonth()]

  if (sameDay) return `${hh}:${mm}`
  if (sameYear) return `${day} ${month} ${hh}:${mm}`
  return `${day} ${month} ${date.getFullYear()}`
}

const expectedDateTimeFormat = (iso: string) => {
  const date = new Date(iso)
  const day = String(date.getDate()).padStart(2, '0')
  const month = MONTHS[date.getMonth()]
  const year = date.getFullYear()
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${day} ${month} ${year} ${hh}:${mm}`
}

const buildTimelineEvents = () => {
  const now = new Date()
  const sameDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 6, 16)
  const sameYear = new Date(now.getFullYear(), now.getMonth() === 0 ? 1 : 0, 9, 6, 16)
  const otherYear = new Date(now.getFullYear() - 1, 1, 9, 6, 16)

  return {
    sameDay,
    sameYear,
    otherYear,
    items: [
      {
        event_type: 'proposal',
        from_state: null,
        to_state: null,
        actor_id: 101,
        payload: {
          price_ton: '10.00',
          ad_type: 'post',
          placement_type: 'post',
          exclusive_hours: 1,
          retention_hours: 24,
          creative_text: 'Counter proposal',
          creative_media_type: 'image',
          creative_media_ref: 'ref-2',
          start_at: '2026-02-10T10:00:00Z',
          posting_params: { hour: 10 },
        },
        created_at: sameDay.toISOString(),
      },
      {
        event_type: 'message',
        from_state: null,
        to_state: null,
        actor_id: 202,
        payload: { text: 'Message body from timeline' },
        created_at: sameYear.toISOString(),
      },
      {
        event_type: 'transition',
        from_state: 'DRAFT',
        to_state: 'NEGOTIATION',
        actor_id: 101,
        payload: { reason: 'proposal' },
        created_at: otherYear.toISOString(),
      },
    ],
  }
}

const mountView = async ({ userId = 202 } = {}) => {
  const pinia = createPinia()
  setActivePinia(pinia)

  const authStore = useAuthStore()
  authStore.bootstrapped = true
  authStore.user = {
    id: userId,
    telegram_user_id: userId + 1000,
    preferred_role: 'advertiser',
    ton_wallet_address: null,
    has_wallet: false,
  }

  const wrapper = mount(DealDetailView, {
    global: {
      plugins: [pinia],
      stubs: {
        teleport: true,
      },
    },
  })

  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('DealDetailView negotiation timeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getMock.mockResolvedValue({ ...baseDeal })
    mocks.updateMock.mockResolvedValue({ ...baseDeal })
    mocks.acceptMock.mockResolvedValue({ ...baseDeal, state: 'CREATIVE_APPROVED' })
    mocks.rejectMock.mockResolvedValue({ ...baseDeal, state: 'REJECTED' })
    mocks.uploadProposalMediaMock.mockResolvedValue({
      creative_media_ref: 'uploaded-ref',
      creative_media_type: 'video',
    })
  })

  it('renders human-formatted timeline and opens message detail modal', async () => {
    const timeline = buildTimelineEvents()
    mocks.eventsMock.mockResolvedValue({ items: timeline.items, next_cursor: null })

    const wrapper = await mountView()

    const timeNodes = wrapper.findAll('.deal__event time')
    expect(timeNodes).toHaveLength(3)
    expect(timeNodes[0].text()).toBe(expectedTimelineFormat(timeline.sameDay))
    expect(timeNodes[1].text()).toBe(expectedTimelineFormat(timeline.sameYear))
    expect(timeNodes[2].text()).toBe(expectedTimelineFormat(timeline.otherYear))

    const actionLabels = wrapper.findAll('button').map((button) => button.text().trim())
    expect(actionLabels).toContain('Edit')
    expect(actionLabels).toContain('Approve')
    expect(actionLabels).toContain('Reject')

    const eventButtons = wrapper.findAll('button.deal__event')
    await eventButtons[1].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Message body from timeline')

    await eventButtons[0].trigger('click')
    await flushPromises()
    expect(wrapper.find('img.deal__event-image').attributes('src')).toContain(
      '/deals/77/proposal/media?media_ref=ref-2',
    )
    expect(wrapper.text()).toContain(expectedDateTimeFormat('2026-02-10T10:00:00Z'))
  })

  it('submits edit proposal and sends approve/reject actions', async () => {
    const timeline = buildTimelineEvents()
    mocks.eventsMock.mockResolvedValue({ items: timeline.items, next_cursor: null })

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    const wrapper = await mountView()

    const editButton = wrapper.findAll('button').find((button) => button.text().trim() === 'Edit')
    expect(editButton).toBeDefined()
    await editButton!.trigger('click')
    await flushPromises()

    await wrapper.find('textarea.deal__textarea').setValue('Updated creative text')
    await wrapper.find('select.deal__select').setValue('video')
    const uploadInput = wrapper.find('input[type="file"]')
    const file = new File(['video-bytes'], 'creative.mp4', { type: 'video/mp4' })
    Object.defineProperty(uploadInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await uploadInput.trigger('change')
    await flushPromises()
    await wrapper.find('input[type="datetime-local"]').setValue('2026-02-10T10:00')

    expect(mocks.uploadProposalMediaMock).toHaveBeenCalledWith(77, file)

    const saveButton = wrapper
      .findAll('button')
      .find((button) => button.text().trim() === 'Save proposal')
    expect(saveButton).toBeDefined()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(mocks.updateMock).toHaveBeenCalledWith(
      77,
      expect.objectContaining({
        creative_text: 'Updated creative text',
        creative_media_type: 'video',
        creative_media_ref: 'uploaded-ref',
      }),
    )

    const approveButton = wrapper
      .findAll('button')
      .find((button) => button.text().trim() === 'Approve')
    expect(approveButton).toBeDefined()
    await approveButton!.trigger('click')
    await flushPromises()
    expect(mocks.acceptMock).toHaveBeenCalledWith(77)

    const rejectButton = wrapper
      .findAll('button')
      .find((button) => button.text().trim() === 'Reject')
    expect(rejectButton).toBeDefined()
    await rejectButton!.trigger('click')
    await flushPromises()
    expect(mocks.rejectMock).toHaveBeenCalledWith(77)

    confirmSpy.mockRestore()
  })

  it('hides proposal action panel for latest proposal sender', async () => {
    const timeline = buildTimelineEvents()
    mocks.eventsMock.mockResolvedValue({ items: timeline.items, next_cursor: null })

    const wrapper = await mountView({ userId: 101 })
    const actionLabels = wrapper.findAll('button').map((button) => button.text().trim())

    expect(actionLabels).not.toContain('Edit')
    expect(actionLabels).not.toContain('Approve')
    expect(actionLabels).not.toContain('Reject')
  })

  it('auto-loads older events when timeline sentinel intersects', async () => {
    const timeline = buildTimelineEvents()
    const olderEvent = {
      event_type: 'proposal',
      from_state: null,
      to_state: null,
      actor_id: 202,
      payload: { creative_text: 'Older proposal' },
      created_at: '2024-01-01T00:00:00Z',
    }

    mocks.eventsMock
      .mockResolvedValueOnce({ items: [timeline.items[0]], next_cursor: 'cursor-older' })
      .mockResolvedValueOnce({ items: [olderEvent], next_cursor: null })

    let observerCallback: IntersectionObserverCallback | null = null
    const observeMock = vi.fn()
    const disconnectMock = vi.fn()
    const originalObserver = (window as typeof window & { IntersectionObserver?: unknown })
      .IntersectionObserver

    ;(window as typeof window & { IntersectionObserver?: unknown }).IntersectionObserver = class {
      constructor(callback: IntersectionObserverCallback) {
        observerCallback = callback
      }

      observe = observeMock
      disconnect = disconnectMock
      unobserve = vi.fn()
      takeRecords = vi.fn(() => [])
      root = null
      rootMargin = ''
      thresholds = []
    }

    const wrapper = await mountView()

    expect(mocks.eventsMock).toHaveBeenNthCalledWith(1, 77, { limit: 20 })
    expect(observeMock).toHaveBeenCalled()

    observerCallback?.(
      [{ isIntersecting: true } as IntersectionObserverEntry],
      {} as IntersectionObserver,
    )
    await flushPromises()

    expect(mocks.eventsMock).toHaveBeenNthCalledWith(2, 77, {
      cursor: 'cursor-older',
      limit: 20,
    })
    const timelineButtons = wrapper.findAll('button.deal__event')
    expect(timelineButtons).toHaveLength(2)
    expect(timelineButtons[0].text()).toContain('proposal')
    expect(timelineButtons[1].text()).toContain('proposal')

    wrapper.unmount()
    ;(window as typeof window & { IntersectionObserver?: unknown }).IntersectionObserver = originalObserver
  })
})
