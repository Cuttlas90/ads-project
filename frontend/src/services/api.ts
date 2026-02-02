const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

const getInitData = () => {
  if (typeof window === 'undefined') return null
  const tgInit = (window as typeof window & { Telegram?: { WebApp?: { initData?: string } } })
    .Telegram?.WebApp?.initData
  if (tgInit) return tgInit
  const params = new URLSearchParams(window.location.search)
  return params.get('initData')
}

const buildHeaders = (body?: BodyInit | null) => {
  const headers: Record<string, string> = {}
  const initData = getInitData()
  if (initData) {
    headers['X-Telegram-Init-Data'] = initData
  }
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  return headers
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (response.ok) {
    return response.json() as Promise<T>
  }
  let message = `Request failed (${response.status})`
  try {
    const payload = await response.json()
    if (payload?.detail) {
      message = payload.detail
    }
  } catch {
    // ignore
  }
  throw new Error(message)
}

export const api = {
  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: buildHeaders(),
    })
    return handleResponse<T>(response)
  },
  async post<T>(path: string, body?: unknown): Promise<T> {
    const payload = body instanceof FormData ? body : body ? JSON.stringify(body) : undefined
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: buildHeaders(payload ?? null),
      body: payload,
    })
    return handleResponse<T>(response)
  },
  async put<T>(path: string, body?: unknown): Promise<T> {
    const payload = body instanceof FormData ? body : body ? JSON.stringify(body) : undefined
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PUT',
      headers: buildHeaders(payload ?? null),
      body: payload,
    })
    return handleResponse<T>(response)
  },
  async patch<T>(path: string, body?: unknown): Promise<T> {
    const payload = body instanceof FormData ? body : body ? JSON.stringify(body) : undefined
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PATCH',
      headers: buildHeaders(payload ?? null),
      body: payload,
    })
    return handleResponse<T>(response)
  },
}
