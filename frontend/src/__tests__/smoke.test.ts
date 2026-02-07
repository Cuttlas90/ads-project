import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach } from 'vitest'

import App from '../App.vue'

beforeEach(() => {
  setActivePinia(createPinia())
})

it('renders app shell', () => {
  const wrapper = mount(App, {
    global: {
      plugins: [createPinia()],
      stubs: ['router-view', 'RouterLink'],
    },
  })
  expect(wrapper.text()).toContain('Telegram Ads')
})
