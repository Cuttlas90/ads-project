const normalizeHex = (value?: string): string | null => {
  if (!value) return null
  const input = value.trim()
  if (!input) return null

  const withHash = input.startsWith('#') ? input : `#${input}`

  if (/^#[0-9a-fA-F]{6}$/.test(withHash)) {
    return withHash.toLowerCase()
  }

  if (/^#[0-9a-fA-F]{3}$/.test(withHash)) {
    const r = withHash[1]
    const g = withHash[2]
    const b = withHash[3]
    return `#${r}${r}${g}${g}${b}${b}`.toLowerCase()
  }

  return null
}

const hexToRgba = (hex: string, alpha: number): string => {
  const normalized = normalizeHex(hex)
  if (!normalized) return `rgba(0, 0, 0, ${alpha})`
  const r = Number.parseInt(normalized.slice(1, 3), 16)
  const g = Number.parseInt(normalized.slice(3, 5), 16)
  const b = Number.parseInt(normalized.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

const resolveThemeParams = (): TelegramThemeParams | null => {
  if (typeof window === 'undefined') {
    return null
  }
  return window.Telegram?.WebApp?.themeParams ?? null
}

const setOrResetCssVar = (name: string, value: string | null) => {
  if (typeof document === 'undefined') {
    return
  }

  const root = document.documentElement
  if (!value) {
    root.style.removeProperty(name)
    return
  }
  root.style.setProperty(name, value)
}

const setTone = (prefix: 'success' | 'warning' | 'danger', fgHex: string | null, alpha: number) => {
  if (!fgHex) {
    setOrResetCssVar(`--app-notif-${prefix}-fg`, null)
    setOrResetCssVar(`--app-notif-${prefix}-bg`, null)
    return
  }

  setOrResetCssVar(`--app-notif-${prefix}-fg`, fgHex)
  setOrResetCssVar(`--app-notif-${prefix}-bg`, hexToRgba(fgHex, alpha))
}

export const applyTelegramThemeTokens = () => {
  const themeParams = resolveThemeParams()
  if (!themeParams) {
    setOrResetCssVar('--app-notif-neutral-bg', null)
    setOrResetCssVar('--app-notif-neutral-fg', null)
    setOrResetCssVar('--app-notif-border', null)
    setTone('success', null, 0.18)
    setTone('warning', null, 0.22)
    setTone('danger', null, 0.18)
    return
  }

  const neutralBg =
    normalizeHex(themeParams.section_bg_color) ||
    normalizeHex(themeParams.secondary_bg_color) ||
    normalizeHex(themeParams.bg_color)
  const neutralFg = normalizeHex(themeParams.text_color)
  const successFg = normalizeHex(themeParams.button_color) || normalizeHex(themeParams.link_color)
  const warningFg = normalizeHex(themeParams.accent_text_color) || normalizeHex(themeParams.link_color)
  const dangerFg = normalizeHex(themeParams.destructive_text_color)
  const border =
    normalizeHex(themeParams.section_separator_color) || normalizeHex(themeParams.hint_color)

  setOrResetCssVar('--app-notif-neutral-bg', neutralBg)
  setOrResetCssVar('--app-notif-neutral-fg', neutralFg)

  setTone('success', successFg, 0.18)
  setTone('warning', warningFg, 0.22)
  setTone('danger', dangerFg, 0.18)

  if (!border) {
    setOrResetCssVar('--app-notif-border', null)
  } else {
    setOrResetCssVar('--app-notif-border', hexToRgba(border, 0.28))
  }
}

export const initTelegramThemeBridge = () => {
  applyTelegramThemeTokens()

  if (typeof window === 'undefined') {
    return () => undefined
  }

  const webApp = window.Telegram?.WebApp
  if (!webApp?.onEvent) {
    return () => undefined
  }

  const onThemeChanged = () => {
    applyTelegramThemeTokens()
  }

  webApp.onEvent('themeChanged', onThemeChanged)

  return () => {
    webApp.offEvent?.('themeChanged', onThemeChanged)
  }
}
