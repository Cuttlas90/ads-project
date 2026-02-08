<template>
  <section class="stats">
    <TgCard title="Channel statistics" subtitle="Read-only analytics snapshot for this channel.">
      <div class="stats__header">
        <p class="stats__channel">{{ channelLabel }}</p>
        <div class="stats__badges">
          <TgBadge tone="neutral">Read-only</TgBadge>
          <TgBadge v-if="statsStore.hasPartialData" tone="warning">Partial data</TgBadge>
        </div>
      </div>
      <p class="stats__meta">Snapshot: {{ capturedAtLabel }}</p>
      <RouterLink class="stats__back" :to="backPath">Back</RouterLink>
    </TgCard>

    <TgCard v-if="statsStore.error" title="Couldn't load statistics">
      <TgStatePanel title="Request failed" :description="statsStore.error">
        <template #icon>!</template>
      </TgStatePanel>
    </TgCard>

    <TgSkeleton v-else-if="statsStore.loading" height="140px" />

    <template v-else-if="stats">
      <TgCard v-if="!stats.snapshot_available" title="No snapshot yet">
        <TgStatePanel
          title="No statistics available"
          description="Run channel verification to capture the first stats snapshot."
        />
      </TgCard>

      <template v-else>
        <TgCard title="Core metrics">
          <div class="stats__metrics">
            <div v-for="metric in readyScalars" :key="metric.key" class="stats__metric-item">
              <p class="stats__metric-key">{{ metric.key }}</p>
              <p class="stats__metric-value">{{ formatMetricValue(metric.value) }}</p>
            </div>
          </div>
        </TgCard>

        <TgCard v-if="unavailableScalars.length" title="Unavailable metrics">
          <div class="stats__missing">
            <TgStatePanel
              v-for="metric in unavailableScalars"
              :key="metric.key"
              :title="metric.key"
              :description="metric.reason || 'No data available in this snapshot.'"
            >
              <template #icon>∅</template>
            </TgStatePanel>
          </div>
        </TgCard>

        <TgCard title="Premium audience">
          <div class="stats__premium">
            <p>
              Ratio:
              <strong>{{ formatRatio(stats.premium_audience.premium_ratio) }}</strong>
            </p>
            <p>
              Premium subscribers:
              <strong>{{ formatMetricValue(stats.premium_audience.part) }}</strong>
            </p>
            <p>
              Total audience:
              <strong>{{ formatMetricValue(stats.premium_audience.total) }}</strong>
            </p>
          </div>
        </TgCard>

        <TgCard v-if="visibleCharts.length" title="Charts">
          <div class="stats__charts">
            <article v-for="chart in visibleCharts" :key="chart.key" class="stats__chart">
              <p class="stats__chart-title">{{ chart.key }}</p>
              <TelegramStatsChart :title="chart.key" :raw-data="chart.data" />
            </article>
          </div>
        </TgCard>
      </template>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import TelegramStatsChart from '../components/charts/TelegramStatsChart.vue'
import { TgBadge, TgCard, TgSkeleton, TgStatePanel } from '../components/tg'
import { useAuthStore } from '../stores/auth'
import { useChannelStatsStore } from '../stores/channelStats'

const route = useRoute()
const authStore = useAuthStore()
const statsStore = useChannelStatsStore()

const channelId = computed(() => Number(route.params.channelId))
const stats = computed(() => statsStore.stats)
const readyScalars = computed(() =>
  (stats.value?.scalar_metrics ?? []).filter((metric) => metric.availability === 'ready'),
)
const unavailableScalars = computed(() => statsStore.unavailableScalars)
const visibleCharts = computed(() => statsStore.visibleCharts)

const channelLabel = computed(
  () => stats.value?.channel_title || stats.value?.channel_username || `Channel #${channelId.value}`,
)
const capturedAtLabel = computed(() => {
  const value = stats.value?.captured_at
  if (!value) return 'Not available'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
})
const backPath = computed(() =>
  authStore.user?.preferred_role === 'owner' ? '/owner' : '/advertiser/marketplace',
)

const loadStats = async () => {
  if (!channelId.value || Number.isNaN(channelId.value)) {
    statsStore.error = 'Invalid channel id'
    return
  }
  await statsStore.fetchStats(channelId.value)
}

const formatMetricValue = (value: unknown): string => {
  if (value === null || value === undefined) return '--'
  if (typeof value === 'number') return Number.isFinite(value) ? value.toLocaleString() : '--'
  return String(value)
}

const formatRatio = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '--'
  return `${(value * 100).toFixed(2)}%`
}

watch(
  () => route.params.channelId,
  () => {
    void loadStats()
  },
)

onMounted(() => {
  void loadStats()
})
</script>

<style scoped>
.stats {
  display: grid;
  gap: 0.85rem;
}

.stats__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
}

.stats__channel {
  margin: 0;
  font-weight: 700;
}

.stats__badges {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.stats__meta {
  margin: 0.5rem 0 0;
  color: var(--app-ink-muted);
}

.stats__back {
  display: inline-block;
  margin-top: 0.65rem;
  font-weight: 600;
  color: var(--app-accent);
}

.stats__metrics {
  display: grid;
  gap: 0.7rem;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.stats__metric-item {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  padding: 0.75rem;
}

.stats__metric-key {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.82rem;
  text-transform: capitalize;
}

.stats__metric-value {
  margin: 0.35rem 0 0;
  font-weight: 700;
}

.stats__missing {
  display: grid;
  gap: 0.65rem;
}

.stats__premium p {
  margin: 0.25rem 0;
}

.stats__charts {
  display: grid;
  gap: 0.75rem;
}

.stats__chart {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  padding: 0.75rem;
}

.stats__chart-title {
  margin: 0 0 0.5rem;
  font-weight: 700;
  text-transform: capitalize;
}

</style>
