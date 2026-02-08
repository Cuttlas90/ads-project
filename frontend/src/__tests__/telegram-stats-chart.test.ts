import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import TelegramStatsChart from '../components/charts/TelegramStatsChart.vue'

describe('TelegramStatsChart', () => {
  it('renders line chart from Telegram DataJSON payload', () => {
    const rawData = {
      _: 'DataJSON',
      data: JSON.stringify({
        columns: [
          ['x', 1762560000000, 1762646400000, 1762732800000, 1762819200000],
          ['y0', 0, 8, 1, 4],
          ['y1', 3, 5, 1, 3],
        ],
        types: { x: 'x', y0: 'line', y1: 'line' },
        names: { y0: 'Joined', y1: 'Left' },
        colors: { y0: 'GREEN#34C759', y1: 'RED#FF3B30' },
      }),
    }

    const wrapper = mount(TelegramStatsChart, {
      props: {
        title: 'growth_graph',
        rawData,
      },
    })

    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.findAll('polyline')).toHaveLength(2)
    expect(wrapper.text()).toContain('Joined')
    expect(wrapper.text()).toContain('Left')
  })

  it('shows unavailable state for unsupported payload', () => {
    const wrapper = mount(TelegramStatsChart, {
      props: {
        title: 'invalid_graph',
        rawData: { unexpected: true },
      },
    })

    expect(wrapper.find('svg').exists()).toBe(false)
    expect(wrapper.text()).toContain('Chart unavailable')
  })
})
