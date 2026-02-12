import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { applyTelegramThemeTokens, initTelegramThemeBridge } from '../services/telegramTheme'

describe('telegram theme bridge', () => {
  beforeEach(() => {
    document.documentElement.style.cssText = ''
    window.Telegram = undefined
  })

  afterEach(() => {
    document.documentElement.style.cssText = ''
    window.Telegram = undefined
  })

  it('applies notification tokens from Telegram themeParams', () => {
    window.Telegram = {
      WebApp: {
        themeParams: {
          section_bg_color: '#112233',
          text_color: '#445566',
          button_color: '#0A8F7A',
          accent_text_color: '#A3561A',
          destructive_text_color: '#D64550',
          section_separator_color: '#777777',
        },
      },
    }

    applyTelegramThemeTokens()

    const rootStyle = document.documentElement.style
    expect(rootStyle.getPropertyValue('--app-notif-neutral-bg')).toBe('#112233')
    expect(rootStyle.getPropertyValue('--app-notif-neutral-fg')).toBe('#445566')
    expect(rootStyle.getPropertyValue('--app-notif-success-fg')).toBe('#0a8f7a')
    expect(rootStyle.getPropertyValue('--app-notif-warning-fg')).toBe('#a3561a')
    expect(rootStyle.getPropertyValue('--app-notif-danger-fg')).toBe('#d64550')
    expect(rootStyle.getPropertyValue('--app-notif-border')).toContain('rgba(')
  })

  it('reacts to themeChanged and unregisters listener', () => {
    let themeChangedHandler: (() => void) | null = null
    const onEvent = vi.fn((eventType: string, handler: () => void) => {
      if (eventType === 'themeChanged') {
        themeChangedHandler = handler
      }
    })
    const offEvent = vi.fn()

    window.Telegram = {
      WebApp: {
        themeParams: {
          button_color: '#0b7a75',
        },
        onEvent,
        offEvent,
      },
    }

    const stop = initTelegramThemeBridge()

    expect(onEvent).toHaveBeenCalledWith('themeChanged', expect.any(Function))
    expect(document.documentElement.style.getPropertyValue('--app-notif-success-fg')).toBe('#0b7a75')

    window.Telegram.WebApp!.themeParams = {
      button_color: '#228B22',
    }
    themeChangedHandler?.()

    expect(document.documentElement.style.getPropertyValue('--app-notif-success-fg')).toBe('#228b22')

    stop()
    expect(offEvent).toHaveBeenCalledWith('themeChanged', expect.any(Function))
  })
})
