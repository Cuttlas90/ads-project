import { mount } from '@vue/test-utils'

import App from '../App.vue'

it('renders app shell', () => {
  const wrapper = mount(App, { global: { stubs: ['router-view', 'RouterLink'] } })
  expect(wrapper.text()).toContain('Telegram Ads')
})
