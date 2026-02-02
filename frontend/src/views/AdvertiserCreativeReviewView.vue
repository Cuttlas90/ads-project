<template>
  <section class="review">
    <TgCard title="Creative review" subtitle="Approve or request edits from the owner.">
      <TgStatePanel v-if="error" title="Unable to load deal" :description="error">
        <template #icon>!</template>
      </TgStatePanel>

      <div v-else-if="deal" class="review__body">
        <div class="review__summary">
          <strong>{{ deal.channel_title || deal.channel_username || 'Channel' }}</strong>
          <p>{{ deal.ad_type }} · {{ deal.price_ton }} TON</p>
        </div>
        <div class="review__creative">
          <p class="label">Text</p>
          <p>{{ deal.creative_text }}</p>
          <p class="label">Media</p>
          <p>{{ deal.creative_media_type }} · {{ deal.creative_media_ref }}</p>
        </div>
        <div class="review__actions">
          <TgButton full-width :loading="loading" @click="approve">Approve</TgButton>
          <TgButton full-width variant="secondary" :loading="loading" @click="requestEdits"
            >Request edits</TgButton
          >
        </div>
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { TgButton, TgCard, TgStatePanel } from '../components/tg'
import { dealsService } from '../services/deals'
import type { DealDetail } from '../types/api'

const route = useRoute()
const dealId = Number(route.params.id)

const deal = ref<DealDetail | null>(null)
const error = ref('')
const loading = ref(false)

const loadDeal = async () => {
  try {
    deal.value = await dealsService.get(dealId)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load deal'
  }
}

const approve = async () => {
  loading.value = true
  error.value = ''
  try {
    await dealsService.approveCreative(dealId)
    await loadDeal()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Approval failed'
  } finally {
    loading.value = false
  }
}

const requestEdits = async () => {
  loading.value = true
  error.value = ''
  try {
    await dealsService.requestEdits(dealId)
    await loadDeal()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Request failed'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadDeal()
})
</script>

<style scoped>
.review__body {
  display: grid;
  gap: 1rem;
}

.review__summary p {
  margin: 0.25rem 0 0 0;
  color: var(--app-ink-muted);
}

.review__creative {
  background: var(--app-surface-muted);
  border-radius: var(--app-radius-md);
  padding: 0.9rem;
}

.review__creative .label {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.7rem;
  color: var(--app-ink-muted);
  margin: 0.5rem 0 0.25rem;
}

.review__actions {
  display: grid;
  gap: 0.75rem;
}
</style>
