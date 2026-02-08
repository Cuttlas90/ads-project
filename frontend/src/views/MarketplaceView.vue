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
        <TgButton full-width :loading="loadingListings" @click="loadListings">Apply filters</TgButton>
      </div>

      <TgStatePanel v-if="error" title="Couldn't load listings" :description="error">
        <template #icon>!</template>
      </TgStatePanel>

      <div v-else class="marketplace__list">
        <TgSkeleton v-if="loadingListings" height="120px" />
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

    <TgModal :open="showModal" title="Start deal" max-width="520px" @close="closeModal">
      <div class="marketplace__modal">
        <p v-if="selectedFormat" class="marketplace__selected">
          Selected: {{ selectedFormat.placement_type }} · {{ selectedFormat.exclusive_hours }}h exclusive ·
          {{ selectedFormat.retention_hours }}h retention · {{ selectedFormat.price }} TON
        </p>
        <label class="marketplace__field">
          <span>Creative text</span>
          <textarea
            v-model="dealForm.creative_text"
            class="marketplace__textarea"
            rows="4"
            placeholder="Write your ad copy"
          ></textarea>
        </label>
        <label class="marketplace__field">
          <span>Media type</span>
          <select v-model="dealForm.creative_media_type" class="marketplace__select">
            <option value="image">Image</option>
            <option value="video">Video</option>
          </select>
        </label>
        <label class="marketplace__upload">
          <span>Media file</span>
          <input
            type="file"
            :accept="dealForm.creative_media_type === 'video' ? 'video/*' : 'image/*'"
            :disabled="uploadingMedia || creatingDeal"
            @change="handleCreativeFile"
          />
        </label>
        <TgBadge v-if="uploadStatus" tone="success">{{ uploadStatus }}</TgBadge>
      </div>
      <template #footer>
        <TgButton
          full-width
          :loading="creatingDeal"
          :disabled="!canCreateDeal || uploadingMedia"
          @click="createDeal"
        >
          Start deal
        </TgButton>
      </template>
    </TgModal>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { TgBadge, TgButton, TgCard, TgInput, TgModal, TgSkeleton, TgStatePanel } from '../components/tg'
import { listingsService } from '../services/listings'
import { marketplaceService } from '../services/marketplace'
import type { MarketplaceListingItem, MarketplaceListingFormat } from '../types/api'

const items = ref<MarketplaceListingItem[]>([])
const loadingListings = ref(false)
const creatingDeal = ref(false)
const uploadingMedia = ref(false)
const error = ref('')
const uploadStatus = ref('')
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

const canCreateDeal = computed(
  () =>
    dealForm.creative_text.trim().length > 0 &&
    dealForm.creative_media_type.trim().length > 0 &&
    dealForm.creative_media_ref.trim().length > 0,
)

const toNumber = (value: string) => {
  if (!value.trim()) return undefined
  const parsed = Number(value)
  if (Number.isNaN(parsed)) return undefined
  return parsed
}

const loadListings = async () => {
  loadingListings.value = true
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
    loadingListings.value = false
  }
}

const resetDealCreative = () => {
  dealForm.creative_text = ''
  dealForm.creative_media_ref = ''
  dealForm.creative_media_type = 'image'
  uploadStatus.value = ''
}

const openDealModal = (listingId: number, format: MarketplaceListingFormat) => {
  dealForm.listing_id = listingId
  dealForm.listing_format_id = format.id
  resetDealCreative()
  selectedFormat.value = format
  showModal.value = true
}

const closeModal = () => {
  selectedFormat.value = null
  showModal.value = false
  resetDealCreative()
}

const handleCreativeFile = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (dealForm.listing_id <= 0) {
    error.value = 'Select a listing format before uploading media.'
    return
  }

  const contentType = file.type || ''
  if (!contentType.startsWith('image/') && !contentType.startsWith('video/')) {
    error.value = 'Please select an image or video file.'
    dealForm.creative_media_ref = ''
    uploadStatus.value = ''
    return
  }

  uploadingMedia.value = true
  error.value = ''
  uploadStatus.value = ''
  dealForm.creative_media_ref = ''
  try {
    const response = await listingsService.uploadCreative(dealForm.listing_id, file)
    dealForm.creative_media_ref = response.creative_media_ref
    dealForm.creative_media_type = response.creative_media_type
    uploadStatus.value = 'Uploaded to Telegram'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Upload failed'
  } finally {
    uploadingMedia.value = false
  }
}

const createDeal = async () => {
  if (!canCreateDeal.value) {
    error.value = 'Please add creative text and upload media before starting deal.'
    return
  }
  creatingDeal.value = true
  error.value = ''
  try {
    await listingsService.createDealFromListing(dealForm.listing_id, {
      listing_format_id: dealForm.listing_format_id,
      creative_text: dealForm.creative_text.trim(),
      creative_media_type: dealForm.creative_media_type,
      creative_media_ref: dealForm.creative_media_ref.trim(),
    })
    closeModal()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to start deal'
  } finally {
    creatingDeal.value = false
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

.marketplace__textarea {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  font-family: inherit;
  background: var(--app-surface);
  color: var(--app-ink);
  resize: vertical;
  min-height: 120px;
}

.marketplace__textarea:focus {
  border-color: var(--app-accent);
  box-shadow: 0 0 0 3px rgba(11, 122, 117, 0.15);
  outline: none;
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

.marketplace__upload {
  display: grid;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: var(--app-ink-muted);
}

.marketplace__upload input {
  border-radius: var(--app-radius-md);
  border: 1px dashed rgba(25, 25, 25, 0.25);
  padding: 0.65rem;
  background: var(--app-surface);
}

.marketplace__selected {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.9rem;
}
</style>
