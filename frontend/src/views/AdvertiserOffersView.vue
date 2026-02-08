<template>
  <section class="offers">
    <TgCard title="Offers" subtitle="Newest offers first across all your campaigns.">
      <TgStatePanel v-if="campaignsStore.error" title="Couldn't load offers" :description="campaignsStore.error">
        <template #icon>!</template>
      </TgStatePanel>

      <TgSkeleton v-else-if="campaignsStore.loadingOffers && !filteredOffers.length" height="96px" />

      <TgStatePanel
        v-else-if="!filteredOffers.length"
        title="No offers yet"
        description="Owner applications will appear here."
      />

      <div v-else class="offers__list">
        <TgCard
          v-for="offer in filteredOffers"
          :key="offer.application_id"
          :title="offer.campaign_title"
          :subtitle="offer.channel_title || offer.channel_username || `Channel ${offer.channel_id}`"
        >
          <p class="offers__meta">
            {{ offer.proposed_format_label }} · {{ offer.status }} · {{ formatTime(offer.created_at) }}
          </p>
          <TgButton
            full-width
            :disabled="offer.status !== 'submitted'"
            @click="openAcceptModal(offer)"
          >
            Accept + create deal
          </TgButton>
        </TgCard>
      </div>
    </TgCard>

    <TgModal :open="showAcceptModal" title="Accept offer" @close="closeAcceptModal">
      <div class="offers__form">
        <p v-if="selectedOffer" class="offers__selected">
          {{ selectedOffer.campaign_title }} ·
          {{ selectedOffer.channel_title || selectedOffer.channel_username || `Channel ${selectedOffer.channel_id}` }}
        </p>
        <TgInput v-model="form.price_ton" label="Price (TON)" type="number" />
        <TgInput v-model="form.ad_type" label="Ad type" placeholder="Post" />
        <TgInput v-model="form.creative_text" label="Creative text" placeholder="Ad copy" />
        <TgInput v-model="form.creative_media_type" label="Media type" placeholder="image or video" />
        <TgInput v-model="form.creative_media_ref" label="Media ref" placeholder="Telegram file_id/ref" />
      </div>
      <template #footer>
        <TgButton full-width :loading="campaignsStore.accepting" @click="acceptOffer">
          Create draft deal
        </TgButton>
      </template>
    </TgModal>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { TgButton, TgCard, TgInput, TgModal, TgSkeleton, TgStatePanel } from '../components/tg'
import { useCampaignsStore } from '../stores/campaigns'
import type { CampaignOfferInboxItem } from '../types/api'

const route = useRoute()
const router = useRouter()
const campaignsStore = useCampaignsStore()

const showAcceptModal = ref(false)
const selectedOffer = ref<CampaignOfferInboxItem | null>(null)

const form = reactive({
  price_ton: '',
  ad_type: 'Post',
  creative_text: '',
  creative_media_type: 'image',
  creative_media_ref: '',
})

const campaignFilterId = computed(() => {
  const value = route.query.campaign_id
  const parsed = Number(value)
  if (Number.isNaN(parsed) || parsed <= 0) {
    return null
  }
  return parsed
})

const filteredOffers = computed(() => {
  const items = campaignsStore.offersPage?.items ?? []
  if (!campaignFilterId.value) {
    return items
  }
  return items.filter((item) => item.campaign_id === campaignFilterId.value)
})

const formatTime = (value: string) => new Date(value).toLocaleString()

const loadOffers = async () => {
  await campaignsStore.fetchOffers()
}

const openAcceptModal = (offer: CampaignOfferInboxItem) => {
  selectedOffer.value = offer
  form.price_ton = ''
  form.ad_type = offer.proposed_format_label || 'Post'
  form.creative_text = ''
  form.creative_media_type = 'image'
  form.creative_media_ref = ''
  showAcceptModal.value = true
}

const closeAcceptModal = () => {
  showAcceptModal.value = false
  selectedOffer.value = null
}

const acceptOffer = async () => {
  if (!selectedOffer.value) {
    return
  }
  if (
    !form.price_ton.trim() ||
    !form.ad_type.trim() ||
    !form.creative_text.trim() ||
    !form.creative_media_type.trim() ||
    !form.creative_media_ref.trim()
  ) {
    campaignsStore.error = 'All accept fields are required.'
    return
  }

  const deal = await campaignsStore.acceptOffer(
    selectedOffer.value.campaign_id,
    selectedOffer.value.application_id,
    {
      price_ton: form.price_ton.trim(),
      ad_type: form.ad_type.trim(),
      creative_text: form.creative_text.trim(),
      creative_media_type: form.creative_media_type.trim(),
      creative_media_ref: form.creative_media_ref.trim(),
    },
  )
  closeAcceptModal()
  await router.push(`/deals/${deal.id}`)
}

onMounted(() => {
  void loadOffers()
})
</script>

<style scoped>
.offers__list {
  display: grid;
  gap: 0.85rem;
}

.offers__meta {
  margin: 0 0 0.75rem;
  color: var(--app-ink-muted);
  font-size: 0.85rem;
}

.offers__form {
  display: grid;
  gap: 0.75rem;
}

.offers__selected {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.9rem;
}
</style>
