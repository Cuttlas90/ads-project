<template>
  <section class="deals">
    <TgCard title="Owner deals" subtitle="Track creative submissions and approvals.">
      <TgStatePanel
        v-if="dealsStore.error"
        title="Couldn't load deals"
        :description="dealsStore.error"
      >
        <template #icon>!</template>
      </TgStatePanel>

      <TgSkeleton v-else-if="dealsStore.loading && !dealsStore.inbox" height="90px" />

      <TgStatePanel
        v-else-if="!dealsStore.inbox || !dealsStore.inbox.items.length"
        title="No deals yet"
        description="Once advertisers request placements, they'll appear here."
      />

      <div v-else class="deals__list">
        <TgCard v-for="deal in dealsStore.inbox.items" :key="deal.id" :padded="false">
          <div class="deals__item">
            <div>
              <strong>{{ deal.channel_title || deal.channel_username || 'Channel' }}</strong>
              <p class="deals__meta">{{ deal.ad_type }} · {{ deal.price_ton }} TON</p>
            </div>
            <TgBadge tone="warning">{{ deal.state }}</TgBadge>
          </div>
          <div class="deals__actions">
            <RouterLink class="deals__link" :to="`/deals/${deal.id}`">View detail</RouterLink>
            <RouterLink
              v-if="['ACCEPTED', 'CREATIVE_CHANGES_REQUESTED'].includes(deal.state)"
              class="deals__link"
              :to="`/owner/deals/${deal.id}/creative`"
            >
              Submit creative
            </RouterLink>
          </div>
        </TgCard>
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import { TgBadge, TgCard, TgSkeleton, TgStatePanel } from '../components/tg'
import { useDealsStore } from '../stores/deals'

const dealsStore = useDealsStore()

onMounted(() => {
  void dealsStore.fetchInbox({ role: 'owner' })
})
</script>

<style scoped>
.deals__list {
  display: grid;
  gap: 0.75rem;
}

.deals__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
}

.deals__meta {
  margin: 0.25rem 0 0 0;
  color: var(--app-ink-muted);
  font-size: 0.85rem;
}

.deals__actions {
  padding: 0 1rem 1rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.deals__link {
  font-weight: 600;
  color: var(--app-accent);
}
</style>
