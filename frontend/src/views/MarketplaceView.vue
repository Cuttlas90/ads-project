<template>
  <section class="marketplace">
    <TgCard title="Marketplace" subtitle="Browse channels and start a deal.">
      <div class="marketplace__filters">
        <TgInput v-model="filters.search" label="Search" placeholder="Channel name" />
        <div class="marketplace__row">
          <TgInput v-model="filters.min_price" label="Min price" type="number" />
          <TgInput v-model="filters.max_price" label="Max price" type="number" />
        </div>
        <TgButton full-width :loading="loading" @click="loadListings">Apply filters</TgButton>
      </div>

      <TgStatePanel v-if="error" title="Couldn't load listings" :description="error">
        <template #icon>!</template>
      </TgStatePanel>

      <div v-else class="marketplace__list">
        <TgSkeleton v-if="loading" height="120px" />
        <TgStatePanel
          v-else-if="!items.length"
          title="No listings"
          description="Try different filters."
        />
        <TgCard v-for="listing in items" :key="listing.listing_id">
          <RouterLink class="marketplace__channel-link" :to="statsRoute(listing.channel_id)">
            {{ listing.channel_title || listing.channel_username || 'Channel' }}
          </RouterLink>
          <p class="marketplace__meta">
            {{ listing.stats.subscribers ?? '--' }} subscribers ·
            {{ listing.stats.avg_views ?? '--' }} avg views
          </p>
          <div class="marketplace__formats">
            <TgButton
              v-for="format in listing.formats"
              :key="format.id"
              size="sm"
              variant="secondary"
              @click="openDealModal(listing.listing_id, format)"
            >
              {{ format.label }} · {{ format.price }} TON
            </TgButton>
          </div>
        </TgCard>
      </div>
    </TgCard>

    <TgModal :open="showModal" title="Start deal" @close="closeModal">
      <div class="marketplace__modal">
        <TgInput
          v-model="dealForm.creative_text"
          label="Creative text"
          placeholder="Write your ad copy"
        />
        <TgInput v-model="dealForm.creative_media_type" label="Media type (image/video)" />
        <TgInput v-model="dealForm.creative_media_ref" label="Media ref (file_id)" />
      </div>
      <template #footer>
        <TgButton full-width :loading="loading" @click="createDeal">Start deal</TgButton>
      </template>
    </TgModal>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { TgButton, TgCard, TgInput, TgModal, TgSkeleton, TgStatePanel } from '../components/tg'
import { listingsService } from '../services/listings'
import { marketplaceService } from '../services/marketplace'
import type { MarketplaceListingItem, MarketplaceListingFormat } from '../types/api'

const items = ref<MarketplaceListingItem[]>([])
const loading = ref(false)
const error = ref('')
const showModal = ref(false)

const filters = reactive({
  search: '',
  min_price: '',
  max_price: '',
})

const dealForm = reactive({
  listing_id: 0,
  listing_format_id: 0,
  creative_text: '',
  creative_media_type: 'image',
  creative_media_ref: '',
})

const loadListings = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await marketplaceService.list({
      search: filters.search || undefined,
      min_price: filters.min_price ? Number(filters.min_price) : undefined,
      max_price: filters.max_price ? Number(filters.max_price) : undefined,
    })
    items.value = response.items
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load listings'
  } finally {
    loading.value = false
  }
}

const openDealModal = (listingId: number, format: MarketplaceListingFormat) => {
  dealForm.listing_id = listingId
  dealForm.listing_format_id = format.id
  dealForm.creative_text = ''
  dealForm.creative_media_ref = ''
  dealForm.creative_media_type = 'image'
  showModal.value = true
}

const statsRoute = (channelId: number) => `/advertiser/channels/${channelId}/stats`

const closeModal = () => {
  showModal.value = false
}

const createDeal = async () => {
  if (!dealForm.creative_text.trim() || !dealForm.creative_media_ref.trim()) {
    error.value = 'Provide creative text and media ref.'
    return
  }
  loading.value = true
  try {
    await listingsService.createDealFromListing(dealForm.listing_id, {
      listing_format_id: dealForm.listing_format_id,
      creative_text: dealForm.creative_text.trim(),
      creative_media_type: dealForm.creative_media_type.trim(),
      creative_media_ref: dealForm.creative_media_ref.trim(),
    })
    showModal.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to start deal'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadListings()
})
</script>

<style scoped>
.marketplace__filters {
  display: grid;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.marketplace__row {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
}

.marketplace__list {
  display: grid;
  gap: 0.85rem;
}

.marketplace__meta {
  margin: 0.35rem 0 0.75rem;
  color: var(--app-ink-muted);
}

.marketplace__channel-link {
  display: inline-block;
  font-weight: 700;
  color: var(--app-accent);
  margin-bottom: 0.35rem;
}

.marketplace__formats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.marketplace__modal {
  display: grid;
  gap: 0.75rem;
}
</style>
