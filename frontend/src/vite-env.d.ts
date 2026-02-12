/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BOT_USERNAME?: string
  readonly VITE_TELEGRAM_VERIFY_USER_USERNAME?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface TelegramThemeParams {
  bg_color?: string
  text_color?: string
  hint_color?: string
  link_color?: string
  button_color?: string
  button_text_color?: string
  secondary_bg_color?: string
  header_bg_color?: string
  bottom_bar_bg_color?: string
  accent_text_color?: string
  section_bg_color?: string
  section_header_text_color?: string
  section_separator_color?: string
  subtitle_text_color?: string
  destructive_text_color?: string
}

interface TelegramWebApp {
  initData?: string
  themeParams?: TelegramThemeParams
  colorScheme?: 'light' | 'dark'
  onEvent?: (eventType: string, eventHandler: () => void) => void
  offEvent?: (eventType: string, eventHandler: () => void) => void
}

interface Window {
  Telegram?: {
    WebApp?: TelegramWebApp
  }
}
