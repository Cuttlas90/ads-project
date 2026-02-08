/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BOT_USERNAME?: string
  readonly VITE_TELEGRAM_VERIFY_USER_USERNAME?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
