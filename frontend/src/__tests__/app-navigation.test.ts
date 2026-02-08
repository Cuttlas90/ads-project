import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import App from '../App.vue'
import { useAuthStore } from '../stores/auth'
import type { RolePreference } from '../types/api'

const mountAppWithRole = (role: RolePreference | null) => {
  const pinia = createPinia()
  setActivePinia(pinia)
  const authStore = useAuthStore()
  authStore.bootstrapped = true
  authStore.user = {
    id: 1,
    telegram_user_id: 99,
    preferred_role: role,
    ton_wallet_address: null,
    has_wallet: false,
  }

  const wrapper = mount(App, {
    global: {
      plugins: [pinia],
      stubs: {
        'router-view': { template: '<div />' },
        RouterLink: {
          props: ['to'],
          template: '<a><slot /></a>',
        },
      },
    },
  })
  return { wrapper, authStore }
}

const navLabels = (wrapper: ReturnType<typeof mount>) =>
  wrapper.findAll('a').map((link) => link.text().trim())

describe('App role-scoped navigation', () => {
  it('renders owner-only navigation links for owner role', () => {
    const { wrapper } = mountAppWithRole('owner')
    expect(navLabels(wrapper)).toEqual(['Owner', 'Campaigns', 'Deals', 'Profile'])
  })

  it('renders advertiser-only navigation links for advertiser role', () => {
    const { wrapper } = mountAppWithRole('advertiser')
    expect(navLabels(wrapper)).toEqual(['Marketplace', 'Campaign', 'Offers', 'Deals', 'Profile'])
  })

  it('updates navigation immediately after role switch', async () => {
    const { wrapper, authStore } = mountAppWithRole('owner')
    authStore.user!.preferred_role = 'advertiser'
    await nextTick()
    expect(navLabels(wrapper)).toEqual(['Marketplace', 'Campaign', 'Offers', 'Deals', 'Profile'])
  })
})
