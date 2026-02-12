import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  routerPushMock: vi.fn(),
  escrowInitMock: vi.fn(),
  tonconnectTxMock: vi.fn(),
  escrowStatusMock: vi.fn(),
  tonConnectCtorMock: vi.fn(),
  sendTransactionMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '42' }, fullPath: '/advertiser/deals/42/fund' }),
  useRouter: () => ({ push: mocks.routerPushMock }),
}))

vi.mock('../services/deals', () => ({
  dealsService: {
    list: vi.fn(),
    get: vi.fn(),
    events: vi.fn(),
    update: vi.fn(),
    accept: vi.fn(),
    reject: vi.fn(),
    submitCreative: vi.fn(),
    approveCreative: vi.fn(),
    requestEdits: vi.fn(),
    uploadCreative: vi.fn(),
    uploadProposalMedia: vi.fn(),
    escrowInit: mocks.escrowInitMock,
    tonconnectTx: mocks.tonconnectTxMock,
    escrowStatus: mocks.escrowStatusMock,
  },
}))

vi.mock('@tonconnect/ui', () => ({
  TonConnectUI: vi.fn().mockImplementation((options: unknown) => {
    mocks.tonConnectCtorMock(options)
    return {
      sendTransaction: mocks.sendTransactionMock,
    }
  }),
}))

import FundingView from '../views/FundingView.vue'
import { useAuthStore } from '../stores/auth'
import { useNotificationsStore } from '../stores/notifications'

const mountView = ({ hasWallet = true }: { hasWallet?: boolean } = {}) => {
  const pinia = createPinia()
  setActivePinia(pinia)

  const authStore = useAuthStore()
  authStore.bootstrapped = true
  authStore.user = {
    id: 10,
    telegram_user_id: 999,
    preferred_role: 'advertiser',
    ton_wallet_address: hasWallet ? '0:abc' : null,
    has_wallet: hasWallet,
  }

  return mount(FundingView, {
    global: {
      plugins: [pinia],
      stubs: {
        teleport: true,
      },
    },
  })
}

describe('FundingView notification policy', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    vi.stubEnv('VITE_TONCONNECT_MANIFEST_URL', 'https://example.com/tonconnect-manifest.json')

    mocks.escrowInitMock.mockResolvedValue({ escrow_id: 1 })
    mocks.tonconnectTxMock.mockResolvedValue({ payload: { validUntil: 1, messages: [] } })
    mocks.escrowStatusMock.mockResolvedValue({
      state: 'AWAITING_DEPOSIT',
      expected_amount_ton: '10',
      received_amount_ton: '0',
      deposit_confirmations: 0,
    })
    mocks.sendTransactionMock.mockResolvedValue({ boc: 'signed' })
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
    vi.unstubAllEnvs()
  })

  it('uses app-handled transaction feedback and disables TONConnect action notifications', async () => {
    const wrapper = mountView()
    await flushPromises()

    const button = wrapper.findAll('button').find((item) => item.text().includes('Generate TONConnect request'))
    expect(button).toBeDefined()

    await button!.trigger('click')
    await flushPromises()

    expect(mocks.tonConnectCtorMock).toHaveBeenCalledWith(
      expect.objectContaining({
        actionsConfiguration: {
          modals: [],
          notifications: [],
        },
      }),
    )

    expect(mocks.sendTransactionMock).toHaveBeenCalledWith(
      { validUntil: 1, messages: [] },
      {
        modals: [],
        notifications: [],
      },
    )

    const notificationsStore = useNotificationsStore()
    expect(notificationsStore.toasts.map((toast) => toast.message)).toContain(
      'Transaction submitted. Waiting for confirmations.',
    )
  })

  it('deduplicates repeated polling failures while keeping inline funding error', async () => {
    mocks.escrowStatusMock.mockRejectedValue(new Error('Failed to fetch escrow status'))

    const wrapper = mountView()
    await flushPromises()

    const button = wrapper.findAll('button').find((item) => item.text().includes('Generate TONConnect request'))
    await button!.trigger('click')
    await flushPromises()

    const notificationsStore = useNotificationsStore()
    const before = notificationsStore.toasts.filter((item) => item.message === 'Failed to fetch escrow status').length

    vi.advanceTimersByTime(4_000)
    await flushPromises()
    vi.advanceTimersByTime(4_000)
    await flushPromises()

    const after = notificationsStore.toasts.filter((item) => item.message === 'Failed to fetch escrow status').length

    expect(wrapper.text()).toContain('Funding issue')
    expect(wrapper.text()).toContain('Failed to fetch escrow status')
    expect(after).toBeLessThanOrEqual(before + 1)
  })
})
