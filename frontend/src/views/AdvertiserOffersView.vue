<template>
  <section class="offers">
    <TgCard title="Offers" subtitle="Newest offers first across all your campaigns.">
      <TgStatePanel v-if="pageError" tone="danger" title="Couldn't load offers" :description="pageError">
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
            {{ offer.proposed_placement_type }} · {{ offer.proposed_exclusive_hours }}h exclusive ·
            {{ offer.proposed_retention_hours }}h retention · {{ offer.status }} ·
            {{ formatTime(offer.created_at) }}
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
        <TgStatePanel v-if="modalError" tone="danger" title="Couldn't create deal" :description="modalError">
          <template #icon>!</template>
        </TgStatePanel>
        <p v-if="selectedOffer" class="offers__selected">
          {{ selectedOffer.campaign_title }} ·
          {{ selectedOffer.channel_title || selectedOffer.channel_username || `Channel ${selectedOffer.channel_id}` }}
        </p>
        <p v-if="selectedOffer" class="offers__terms">
          Terms: {{ selectedOffer.proposed_placement_type }} ·
          {{ selectedOffer.proposed_exclusive_hours }}h exclusive ·
          {{ selectedOffer.proposed_retention_hours }}h retention
        </p>
        <label class="offers__field">
          <span>Creative text</span>
          <textarea
            v-model="form.creative_text"
            class="offer__textarea"
            rows="4"
            placeholder="Write your ad copy"
          ></textarea>
          <p v-if="fieldErrors.creativeText" class="offers__field-error">{{ fieldErrors.creativeText }}</p>
        </label>
        <TgInput v-model="form.start_at" label="Start at" type="datetime-local" />
        <label class="offers__field">
          <span>Media type</span>
          <select v-model="form.creative_media_type" class="offers__select">
            <option value="image">Image</option>
            <option value="video">Video</option>
          </select>
        </label>
        <label class="offers__upload">
          <span>Media file</span>
          <input
            type="file"
            :accept="form.creative_media_type === 'video' ? 'video/*' : 'image/*'"
            :disabled="uploadingMedia || campaignsStore.accepting"
            @change="handleCreativeFile"
          />
          <p v-if="fieldErrors.creativeMedia" class="offers__field-error">{{ fieldErrors.creativeMedia }}</p>
          <p v-if="form.creative_media_ref" class="offers__field-hint">Media uploaded and ready.</p>
        </label>
      </div>
      <template #footer>
        <TgButton
          full-width
          :loading="campaignsStore.accepting"
          :disabled="!canCreateDeal || uploadingMedia"
          @click="acceptOffer"
        >
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
import { campaignsService } from '../services/campaigns'
import { useCampaignsStore } from '../stores/campaigns'
import { useNotificationsStore } from '../stores/notifications'
import type { CampaignOfferInboxItem } from '../types/api'

const route = useRoute()
const router = useRouter()
const campaignsStore = useCampaignsStore()
const notificationsStore = useNotificationsStore()

const showAcceptModal = ref(false)
const selectedOffer = ref<CampaignOfferInboxItem | null>(null)
const uploadingMedia = ref(false)
const pageError = ref('')
const modalError = ref('')

const form = reactive({
  creative_text: '',
  start_at: '',
  creative_media_type: 'image',
  creative_media_ref: '',
})

const fieldErrors = reactive({
  creativeText: '',
  creativeMedia: '',
})

const canCreateDeal = computed(
  () =>
    form.creative_text.trim().length > 0 &&
    form.creative_media_type.trim().length > 0 &&
    form.creative_media_ref.trim().length > 0,
)

const toIsoDateTime = (value: string) => {
  const trimmed = value.trim()
  if (!trimmed) return undefined
  const parsed = new Date(trimmed)
  if (Number.isNaN(parsed.getTime())) return undefined
  return parsed.toISOString()
}

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
  pageError.value = campaignsStore.error ?? ''
  campaignsStore.clearError()
}

const resetFieldErrors = () => {
  fieldErrors.creativeText = ''
  fieldErrors.creativeMedia = ''
}

const openAcceptModal = (offer: CampaignOfferInboxItem) => {
  selectedOffer.value = offer
  form.creative_text = ''
  form.start_at = ''
  form.creative_media_type = 'image'
  form.creative_media_ref = ''
  modalError.value = ''
  resetFieldErrors()
  campaignsStore.clearError()
  showAcceptModal.value = true
}

const closeAcceptModal = () => {
  showAcceptModal.value = false
  selectedOffer.value = null
  modalError.value = ''
  resetFieldErrors()
  campaignsStore.clearError()
}

const handleCreativeFile = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file || !selectedOffer.value) return

  const contentType = file.type || ''
  if (!contentType.startsWith('image/') && !contentType.startsWith('video/')) {
    fieldErrors.creativeMedia = 'Please select an image or video file.'
    form.creative_media_ref = ''
    return
  }

  uploadingMedia.value = true
  modalError.value = ''
  fieldErrors.creativeMedia = ''
  campaignsStore.clearError()
  form.creative_media_ref = ''
  try {
    const response = await campaignsService.uploadCreative(
      selectedOffer.value.campaign_id,
      selectedOffer.value.application_id,
      file,
    )
    form.creative_media_ref = response.creative_media_ref
    form.creative_media_type = response.creative_media_type
    notificationsStore.pushToast({
      tone: 'success',
      source: 'offers-modal',
      message: 'Creative media uploaded to Telegram.',
    })
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : 'Upload failed'
  } finally {
    uploadingMedia.value = false
  }
}

const acceptOffer = async () => {
  if (!selectedOffer.value) {
    return
  }
  modalError.value = ''
  resetFieldErrors()
  if (!form.creative_text.trim()) {
    fieldErrors.creativeText = 'Please add creative text.'
  }
  if (!form.creative_media_ref.trim()) {
    fieldErrors.creativeMedia = 'Please upload an image or video before creating deal.'
  }
  if (!canCreateDeal.value) {
    if (!fieldErrors.creativeText && !fieldErrors.creativeMedia) {
      modalError.value = 'Please add creative text and upload media before creating deal.'
    }
    return
  }

  try {
    const deal = await campaignsStore.acceptOffer(
      selectedOffer.value.campaign_id,
      selectedOffer.value.application_id,
      {
        creative_text: form.creative_text.trim(),
        start_at: toIsoDateTime(form.start_at),
        creative_media_type: form.creative_media_type,
        creative_media_ref: form.creative_media_ref.trim(),
      },
    )
    notificationsStore.pushToast({
      tone: 'success',
      source: 'offers-modal',
      message: 'Draft deal created successfully.',
    })
    closeAcceptModal()
    await router.push(`/deals/${deal.id}`)
  } catch {
    modalError.value = campaignsStore.error ?? 'Failed to accept offer'
    campaignsStore.clearError()
  }
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

.offer__textarea {
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

.offers__terms {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.85rem;
}

.offers__field {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.offers__field > span {
  color: var(--app-ink-muted);
  font-weight: 600;
}

.offers__select {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  background: var(--app-surface);
  color: var(--app-ink);
}

.offers__upload {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.offers__upload > span {
  color: var(--app-ink-muted);
  font-weight: 600;
}

.offers__upload input[type='file'] {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.55rem 0.7rem;
  font-size: 0.9rem;
  background: var(--app-surface);
  color: var(--app-ink);
}

.offers__field-error {
  margin: 0;
  color: var(--app-notif-danger-fg);
  font-size: 0.82rem;
  font-weight: 600;
}

.offers__field-hint {
  margin: 0;
  color: var(--app-notif-success-fg);
  font-size: 0.82rem;
  font-weight: 600;
}
</style>
