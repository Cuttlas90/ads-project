import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const parseAllowedHosts = (raw: string | undefined): string[] => {
  if (!raw) return []
  return raw
    .split(',')
    .map((host) => host.trim())
    .filter(Boolean)
}

const allowedHosts = parseAllowedHosts(process.env.VITE_ALLOWED_HOSTS || process.env.ALLOWED_HOSTS)

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: allowedHosts.length > 0 ? allowedHosts : ['localhost', '127.0.0.1', 'app.chainofwinners.com'],
  },
})
