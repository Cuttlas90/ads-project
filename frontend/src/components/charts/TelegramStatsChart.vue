<template>
  <div class="tg-chart">
    <svg
      v-if="renderModel"
      class="tg-chart__svg"
      :viewBox="`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`"
      role="img"
      :aria-label="title"
    >
      <g>
        <line
          v-for="line in gridLines"
          :key="line.y"
          :x1="PADDING_LEFT"
          :x2="SVG_WIDTH - PADDING_RIGHT"
          :y1="line.y"
          :y2="line.y"
          class="tg-chart__grid"
        />
      </g>

      <g>
        <polyline
          v-for="series in renderModel.series"
          :key="series.id"
          :points="series.points"
          fill="none"
          :stroke="series.color"
          stroke-width="2.25"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </g>

      <g class="tg-chart__axis">
        <text :x="PADDING_LEFT - 6" :y="PADDING_TOP + 4" text-anchor="end">
          {{ formatNumber(renderModel.yMax) }}
        </text>
        <text
          :x="PADDING_LEFT - 6"
          :y="SVG_HEIGHT - PADDING_BOTTOM"
          text-anchor="end"
          alignment-baseline="ideographic"
        >
          {{ formatNumber(renderModel.yMin) }}
        </text>

        <text
          v-for="tick in xTicks"
          :key="`${tick.label}-${tick.x}`"
          :x="tick.x"
          :y="SVG_HEIGHT - 6"
          text-anchor="middle"
        >
          {{ tick.label }}
        </text>
      </g>
    </svg>

    <TgStatePanel
      v-else
      title="Chart unavailable"
      description="The chart payload is missing or has an unsupported format."
    >
      <template #icon>∅</template>
    </TgStatePanel>

    <ul v-if="renderModel" class="tg-chart__legend">
      <li v-for="series in renderModel.series" :key="series.id" class="tg-chart__legend-item">
        <span class="tg-chart__legend-dot" :style="{ backgroundColor: series.color }" />
        <span>{{ series.name }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { TgStatePanel } from '../tg'

interface Props {
  title: string
  rawData: unknown
}

interface ParsedSeries {
  id: string
  name: string
  color: string
  values: number[]
}

interface ParsedChart {
  xValues: number[]
  series: ParsedSeries[]
  yMin: number
  yMax: number
}

interface RenderSeries extends ParsedSeries {
  points: string
}

interface RenderChart {
  xValues: number[]
  yMin: number
  yMax: number
  series: RenderSeries[]
}

interface ChartPayload {
  columns: unknown[]
  types?: Record<string, unknown>
  names?: Record<string, unknown>
  colors?: Record<string, unknown>
  hidden?: unknown[]
}

const props = defineProps<Props>()

const SVG_WIDTH = 760
const SVG_HEIGHT = 280
const PADDING_LEFT = 40
const PADDING_RIGHT = 12
const PADDING_TOP = 14
const PADDING_BOTTOM = 28

const parsedChart = computed(() => parseTelegramChart(props.rawData))

const renderModel = computed<RenderChart | null>(() => {
  const chart = parsedChart.value
  if (!chart) return null
  return {
    xValues: chart.xValues,
    yMin: chart.yMin,
    yMax: chart.yMax,
    series: chart.series.map((series) => ({
      ...series,
      points: toPolylinePoints(series.values, chart),
    })),
  }
})

const gridLines = computed(() => {
  const chart = renderModel.value
  if (!chart) return []
  const steps = 4
  return Array.from({ length: steps + 1 }, (_, index) => {
    const ratio = index / steps
    const y = PADDING_TOP + ratio * plotHeight()
    return { y }
  })
})

const xTicks = computed(() => {
  const chart = renderModel.value
  if (!chart || chart.xValues.length === 0) return []

  const indices =
    chart.xValues.length === 1
      ? [0]
      : Array.from(new Set([0, Math.floor(chart.xValues.length / 2), chart.xValues.length - 1]))

  return indices.map((index) => ({
    x: xCoordinate(index, chart.xValues.length),
    label: formatDateTick(chart.xValues[index]),
  }))
})

const plotWidth = () => SVG_WIDTH - PADDING_LEFT - PADDING_RIGHT
const plotHeight = () => SVG_HEIGHT - PADDING_TOP - PADDING_BOTTOM

const formatNumber = (value: number): string =>
  new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 }).format(value)

function formatDateTick(value: number): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function xCoordinate(index: number, length: number): number {
  if (length <= 1) return PADDING_LEFT + plotWidth() / 2
  return PADDING_LEFT + (index / (length - 1)) * plotWidth()
}

function yCoordinate(value: number, min: number, max: number): number {
  if (max <= min) return PADDING_TOP + plotHeight() / 2
  const ratio = (value - min) / (max - min)
  return PADDING_TOP + (1 - ratio) * plotHeight()
}

function toPolylinePoints(values: number[], chart: ParsedChart): string {
  return values
    .map((value, index) => {
      const x = xCoordinate(index, values.length)
      const y = yCoordinate(value, chart.yMin, chart.yMax)
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
}

function parseTelegramChart(raw: unknown): ParsedChart | null {
  const payload = toChartPayload(raw)
  if (!payload) return null

  const types = normalizeRecord(payload.types)
  const names = normalizeRecord(payload.names)
  const colors = normalizeRecord(payload.colors)
  const hidden = new Set((Array.isArray(payload.hidden) ? payload.hidden : []).map((item) => String(item)))

  const xKey = Object.entries(types).find(([, type]) => type === 'x')?.[0] ?? 'x'
  const columns = Array.isArray(payload.columns) ? payload.columns : []
  const xColumn = columns.find((column) => Array.isArray(column) && String(column[0]) === xKey)
  if (!Array.isArray(xColumn)) return null

  const xValues = xColumn.slice(1).map(toNumber).filter((value): value is number => value !== null)
  if (xValues.length === 0) return null

  const series: ParsedSeries[] = []
  for (const column of columns) {
    if (!Array.isArray(column) || column.length < 2) continue
    const id = String(column[0])
    if (id === xKey || hidden.has(id)) continue

    const yType = types[id]
    if (yType === 'x') continue

    const values = column
      .slice(1)
      .map(toNumber)
      .filter((value): value is number => value !== null)

    if (values.length !== xValues.length) continue
    if (!values.length) continue

    series.push({
      id,
      name: typeof names[id] === 'string' ? names[id] : id,
      color: toColor(colors[id], series.length),
      values,
    })
  }

  if (!series.length) return null
  const yAll = series.flatMap((item) => item.values)
  const yMin = Math.min(...yAll)
  const yMax = Math.max(...yAll)

  return {
    xValues,
    series,
    yMin: yMin === yMax ? yMin - 1 : yMin,
    yMax: yMin === yMax ? yMax + 1 : yMax,
  }
}

function toChartPayload(raw: unknown): ChartPayload | null {
  const candidate = unwrapDataJson(raw)
  if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return null
  if (!Array.isArray((candidate as ChartPayload).columns)) return null
  return candidate as ChartPayload
}

function unwrapDataJson(raw: unknown): unknown {
  if (typeof raw === 'string') {
    try {
      return unwrapDataJson(JSON.parse(raw))
    } catch {
      return null
    }
  }

  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null
  const value = raw as Record<string, unknown>

  if (value._ === 'DataJSON') {
    return unwrapDataJson(value.data)
  }

  if (value.data && typeof value.data === 'string') {
    try {
      return unwrapDataJson(JSON.parse(value.data))
    } catch {
      // Fall through: this might already be the final chart payload.
    }
  }

  if (value.json) {
    return unwrapDataJson(value.json)
  }

  return value
}

function normalizeRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function toNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function toColor(value: unknown, index: number): string {
  if (typeof value === 'string') {
    const hex = value.match(/#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})/)
    if (hex) return hex[0]
    if (/^[a-zA-Z]+$/.test(value.trim())) return value.trim()
  }

  const palette = ['#34C759', '#FF3B30', '#0A84FF', '#FF9F0A', '#5856D6', '#64D2FF', '#30D158']
  return palette[index % palette.length]
}
</script>

<style scoped>
.tg-chart {
  display: grid;
  gap: 0.75rem;
}

.tg-chart__svg {
  width: 100%;
  height: auto;
  min-height: 190px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(244, 246, 248, 0.75));
}

.tg-chart__grid {
  stroke: rgba(25, 25, 25, 0.12);
  stroke-width: 1;
}

.tg-chart__axis {
  fill: var(--app-ink-muted);
  font-size: 11px;
}

.tg-chart__legend {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.tg-chart__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--app-ink-muted);
  font-size: 0.82rem;
}

.tg-chart__legend-dot {
  width: 0.58rem;
  height: 0.58rem;
  border-radius: 999px;
}
</style>
