import { defineStore } from 'pinia'

export type NotificationTone = 'neutral' | 'success' | 'warning' | 'danger'

interface NotificationToast {
  id: number
  message: string
  tone: NotificationTone
  dismissible: boolean
  dedupeKey: string
  source?: string
  createdAt: number
  durationMs: number
}

interface PushToastInput {
  message: string
  tone?: NotificationTone
  dismissible?: boolean
  source?: string
  dedupeKey?: string
  durationMs?: number
}

interface NotificationsState {
  toasts: NotificationToast[]
  dedupeWindowMs: number
  maxVisible: number
  lastSeenByKey: Record<string, number>
}

const DEFAULT_DURATION_BY_TONE: Record<NotificationTone, number> = {
  neutral: 4_000,
  success: 5_000,
  warning: 6_000,
  danger: 7_000,
}

let nextToastId = 1
const timers = new Map<number, number>()

const resolveTone = (tone?: NotificationTone): NotificationTone => tone ?? 'neutral'

const buildDedupeKey = (payload: PushToastInput, tone: NotificationTone) =>
  payload.dedupeKey ?? `${payload.source ?? 'app'}|${tone}|${payload.message}`

export const useNotificationsStore = defineStore('notifications', {
  state: (): NotificationsState => ({
    toasts: [],
    dedupeWindowMs: 4_000,
    maxVisible: 3,
    lastSeenByKey: {},
  }),
  actions: {
    pushToast(payload: PushToastInput): number | null {
      const tone = resolveTone(payload.tone)
      const now = Date.now()
      const dedupeKey = buildDedupeKey(payload, tone)
      const lastSeen = this.lastSeenByKey[dedupeKey]

      if (typeof lastSeen === 'number' && now - lastSeen <= this.dedupeWindowMs) {
        return null
      }

      this.lastSeenByKey[dedupeKey] = now

      // Keep dedupe map bounded to recent events only.
      Object.entries(this.lastSeenByKey).forEach(([key, seenAt]) => {
        if (now - seenAt > this.dedupeWindowMs * 3) {
          delete this.lastSeenByKey[key]
        }
      })

      const id = nextToastId++
      const durationMs = payload.durationMs ?? DEFAULT_DURATION_BY_TONE[tone]
      const toast: NotificationToast = {
        id,
        message: payload.message,
        tone,
        dismissible: payload.dismissible ?? true,
        dedupeKey,
        source: payload.source,
        createdAt: now,
        durationMs,
      }

      this.toasts = [...this.toasts, toast]

      if (this.toasts.length > this.maxVisible) {
        const overflow = this.toasts.length - this.maxVisible
        const removed = this.toasts.splice(0, overflow)
        removed.forEach((item) => {
          const timer = timers.get(item.id)
          if (typeof timer === 'number') {
            window.clearTimeout(timer)
            timers.delete(item.id)
          }
        })
      }

      if (durationMs > 0) {
        const timer = window.setTimeout(() => {
          this.dismissToast(id)
        }, durationMs)
        timers.set(id, timer)
      }

      return id
    },
    dismissToast(id: number) {
      const next = this.toasts.filter((item) => item.id !== id)
      if (next.length === this.toasts.length) {
        return
      }
      this.toasts = next
      const timer = timers.get(id)
      if (typeof timer === 'number') {
        window.clearTimeout(timer)
        timers.delete(id)
      }
    },
    clearToasts() {
      this.toasts.forEach((item) => {
        const timer = timers.get(item.id)
        if (typeof timer === 'number') {
          window.clearTimeout(timer)
          timers.delete(item.id)
        }
      })
      this.toasts = []
    },
  },
})
