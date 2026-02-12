import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useNotificationsStore } from '../stores/notifications'

describe('notifications store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
  })

  it('auto-dismisses toasts using tone durations', () => {
    const store = useNotificationsStore()

    store.pushToast({ message: 'Neutral toast', tone: 'neutral' })
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(3_999)
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(store.toasts).toHaveLength(0)

    store.pushToast({ message: 'Success toast', tone: 'success' })
    vi.advanceTimersByTime(4_999)
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(store.toasts).toHaveLength(0)

    store.pushToast({ message: 'Warning toast', tone: 'warning' })
    vi.advanceTimersByTime(5_999)
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(store.toasts).toHaveLength(0)

    store.pushToast({ message: 'Danger toast', tone: 'danger' })
    vi.advanceTimersByTime(6_999)
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(store.toasts).toHaveLength(0)
  })

  it('suppresses duplicate events inside dedupe window', () => {
    const store = useNotificationsStore()

    const firstId = store.pushToast({
      message: 'Failed to fetch escrow status',
      tone: 'warning',
      source: 'funding',
    })
    const secondId = store.pushToast({
      message: 'Failed to fetch escrow status',
      tone: 'warning',
      source: 'funding',
    })

    expect(firstId).toBeTypeOf('number')
    expect(secondId).toBeNull()
    expect(store.toasts).toHaveLength(1)

    vi.advanceTimersByTime(store.dedupeWindowMs + 1)

    const thirdId = store.pushToast({
      message: 'Failed to fetch escrow status',
      tone: 'warning',
      source: 'funding',
    })

    expect(thirdId).toBeTypeOf('number')
    expect(store.toasts).toHaveLength(2)
  })

  it('enforces max-visible stack and removes oldest toasts first', () => {
    const store = useNotificationsStore()
    store.maxVisible = 2

    store.pushToast({ message: 'Toast A', tone: 'neutral', durationMs: 30_000 })
    store.pushToast({ message: 'Toast B', tone: 'neutral', durationMs: 30_000 })
    store.pushToast({ message: 'Toast C', tone: 'neutral', durationMs: 30_000 })

    expect(store.toasts.map((item) => item.message)).toEqual(['Toast B', 'Toast C'])
  })
})
