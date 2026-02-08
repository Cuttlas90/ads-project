<template>
  <section class="marketplace">
    <TgCard title="Marketplace" subtitle="Browse channels and start a deal.">
      <div class="marketplace__filters">
        <TgInput v-model="filters.search" label="Search" placeholder="Channel name" />
        <div class="marketplace__row">
          <TgInput v-model="filters.min_price" label="Min price" type="number" />
          <TgInput v-model="filters.max_price" label="Max price" type="number" />
        </div>
        <label class="marketplace__field">
          <span>Placement type</span>
          <select v-model="filters.placement_type" class="marketplace__select">
            <option value="">Any</option>
            <option value="post">Post</option>
            <option value="story">Story</option>
          </select>
        </label>
        <div class="marketplace__row">
          <TgInput v-model="filters.min_exclusive_hours" label="Min exclusive hours" type="number" />
          <TgInput v-model="filters.max_exclusive_hours" label="Max exclusive hours" type="number" />
        </div>
        <div class="marketplace__row">
          <TgInput v-model="filters.min_retention_hours" label="Min retention hours" type="number" />
          <TgInput v-model="filters.max_retention_hours" label="Max retention hours" type="number" />
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
        <TgCard
          v-for="listing in items"
          :key="listing.listing_id"
          :title="listing.channel_title || listing.channel_username || 'Channel'"
        >
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
              {{ format.placement_type }} · {{ format.exclusive_hours }}h exclusive ·
              {{ format.retention_hours }}h retention · {{ format.price }} TON
            </TgButton>
          </div>
        </TgCard>
      </div>
    </TgCard>

    <TgModal :open="showModal" title="Start deal" @close="closeModal">
      <div class="marketplace__modal">
        <p v-if="selectedFormat" class="marketplace__selected">
          Selected: {{ selectedFormat.placement_type }} · {{ selectedFormat.exclusive_hours }}h exclusive ·
          {{ selectedFormat.retention_hours }}h retention · {{ selectedFormat.price }} TON
        </p>
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

import { TgButton, TgCard, TgInput, TgModal, TgSkeleton, TgStatePanel } from '../components/tg'
import { listingsService } from '../services/listings'
import { marketplaceService } from '../services/marketplace'
import type { MarketplaceListingItem, MarketplaceListingFormat } from '../types/api'

const items = ref<MarketplaceListingItem[]>([])
const loading = ref(false)
const error = ref('')
const showModal = ref(false)
const selectedFormat = ref<MarketplaceListingFormat | null>(null)

const filters = reactive({
  search: '',
  min_price: '',
  max_price: '',
  placement_type: '' as '' | 'post' | 'story',
  min_exclusive_hours: '',
  max_exclusive_hours: '',
  min_retention_hours: '',
  max_retention_hours: '',
})

const dealForm = reactive({
  listing_id: 0,
  listing_format_id: 0,
  creative_text: '',
  creative_media_type: 'image',
  creative_media_ref: '',
})

const toNumber = (value: string) => {
  if (!value.trim()) return undefined
  const parsed = Number(value)
  if (Number.isNaN(parsed)) return undefined
  return parsed
}

const loadListings = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await marketplaceService.list({
      search: filters.search || undefined,
      min_price: toNumber(filters.min_price),
      max_price: toNumber(filters.max_price),
      placement_type: filters.placement_type || undefined,
      min_exclusive_hours: toNumber(filters.min_exclusive_hours),
      max_exclusive_hours: toNumber(filters.max_exclusive_hours),
      min_retention_hours: toNumber(filters.min_retention_hours),
      max_retention_hours: toNumber(filters.max_retention_hours),
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
  selectedFormat.value = format
  showModal.value = true
}

const closeModal = () => {
  selectedFormat.value = null
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
    selectedFormat.value = null
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

.marketplace__field {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.marketplace__field > span {
  color: var(--app-ink-muted);
  font-weight: 600;
}

.marketplace__select {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  background: var(--app-surface);
  color: var(--app-ink);
}

.marketplace__list {
  display: grid;
  gap: 0.85rem;
}

.marketplace__meta {
  margin: 0.35rem 0 0.75rem;
  color: var(--app-ink-muted);
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

.marketplace__selected {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.9rem;
}
</style>
