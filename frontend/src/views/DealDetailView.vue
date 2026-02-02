<template>
  <section class="deal">
    <TgCard title="Deal detail" subtitle="Timeline and next actions.">
      <TgStatePanel v-if="error" title="Unable to load deal" :description="error">
        <template #icon>!</template>
      </TgStatePanel>

      <div v-else-if="deal" class="deal__content">
        <div class="deal__summary">
          <div>
            <strong>{{ deal.channel_title || deal.channel_username || 'Channel' }}</strong>
            <p>{{ deal.ad_type }} · {{ deal.price_ton }} TON</p>
          </div>
          <TgBadge tone="warning">{{ deal.state }}</TgBadge>
        </div>

        <TgList title="Timeline">
          <TgCard
            v-for="event in events"
            :key="event.created_at + event.event_type"
            :padded="false"
          >
            <div class="deal__event">
              <strong>{{ event.event_type }}</strong>
              <p>{{ event.created_at }}</p>
            </div>
          </TgCard>
        </TgList>

        <div class="deal__actions">
          <TgButton v-if="actionLink" full-width :variant="actionVariant" @click="navigateAction">
            {{ actionLabel }}
          </TgButton>
          <a class="deal__bot" :href="botLink" target="_blank" rel="noreferrer"
            >Open bot messages</a
          >
        </div>
      </div>

      <TgSkeleton v-else height="120px" />
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { TgBadge, TgButton, TgCard, TgList, TgSkeleton, TgStatePanel } from '../components/tg'
import { dealsService } from '../services/deals'
import { useAuthStore } from '../stores/auth'
import type { DealDetail, DealTimelineEvent } from '../types/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const dealId = Number(route.params.id)
const deal = ref<DealDetail | null>(null)
const events = ref<DealTimelineEvent[]>([])
const error = ref('')

const role = computed(
  () => authStore.user?.preferred_role || (route.query.role as string | undefined),
)

const loadDeal = async () => {
  try {
    deal.value = await dealsService.get(dealId)
    const timeline = await dealsService.events(dealId)
    events.value = timeline.items
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load deal'
  }
}

const actionLabel = computed(() => {
  if (!deal.value || !role.value) return ''
  if (
    role.value === 'owner' &&
    ['ACCEPTED', 'CREATIVE_CHANGES_REQUESTED'].includes(deal.value.state)
  ) {
    return 'Submit creative'
  }
  if (role.value === 'advertiser' && deal.value.state === 'CREATIVE_SUBMITTED') {
    return 'Review creative'
  }
  if (role.value === 'advertiser' && deal.value.state === 'CREATIVE_APPROVED') {
    return 'Fund escrow'
  }
  return ''
})

const actionLink = computed(() => {
  if (!deal.value || !role.value) return ''
  if (
    role.value === 'owner' &&
    ['ACCEPTED', 'CREATIVE_CHANGES_REQUESTED'].includes(deal.value.state)
  ) {
    return `/owner/deals/${dealId}/creative`
  }
  if (role.value === 'advertiser' && deal.value.state === 'CREATIVE_SUBMITTED') {
    return `/advertiser/deals/${dealId}/review`
  }
  if (role.value === 'advertiser' && deal.value.state === 'CREATIVE_APPROVED') {
    return `/advertiser/deals/${dealId}/fund`
  }
  return ''
})

const actionVariant = computed(() => (actionLabel.value ? 'primary' : 'secondary'))

const navigateAction = () => {
  if (actionLink.value) {
    void router.push(actionLink.value)
  }
}

const botLink = computed(() => {
  const botUsername = import.meta.env.VITE_BOT_USERNAME || 'tgads_bot'
  return `https://t.me/${botUsername}?start=deal_${dealId}`
})

onMounted(() => {
  void authStore.fetchMe()
  void loadDeal()
})
</script>

<style scoped>
.deal__content {
  display: grid;
  gap: 1rem;
}

.deal__summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.deal__summary p {
  margin: 0.3rem 0 0;
  color: var(--app-ink-muted);
}

.deal__event {
  padding: 0.9rem;
  display: flex;
  justify-content: space-between;
  color: var(--app-ink-muted);
}

.deal__actions {
  display: grid;
  gap: 0.75rem;
}

.deal__bot {
  font-weight: 600;
  color: var(--app-accent);
  text-align: center;
}
</style>
