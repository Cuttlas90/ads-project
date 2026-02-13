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

        <div class="deal__actions">
          <div v-if="showNegotiationActions" class="deal__proposal-actions">
            <TgButton class="deal__action-btn deal__action-btn--edit" :loading="actionLoading" @click="openEditModal">
              Edit
            </TgButton>
            <TgButton class="deal__action-btn deal__action-btn--approve" :loading="actionLoading" @click="approveProposal">
              Approve
            </TgButton>
            <TgButton class="deal__action-btn deal__action-btn--reject" :loading="actionLoading" @click="rejectProposal">
              Reject
            </TgButton>
          </div>

          <TgButton v-if="actionLink" full-width :variant="actionVariant" @click="navigateAction">
            {{ actionLabel }}
          </TgButton>

          <a class="deal__bot" :href="botLink" target="_blank" rel="noreferrer">Open bot messages</a>
        </div>

        <TgList title="Timeline">
          <TgCard
            v-for="(event, index) in events"
            :key="`${event.created_at}-${event.event_type}-${event.actor_id ?? 'na'}-${index}`"
            :padded="false"
          >
            <button class="deal__event" type="button" @click="openEvent(event)">
              <strong>{{ event.event_type }}</strong>
              <time :datetime="event.created_at">{{ formatTimelineTime(event.created_at) }}</time>
            </button>
          </TgCard>
        </TgList>

        <p v-if="loadingOlder" class="deal__timeline-status">Loading older events...</p>
        <div ref="timelineSentinel" class="deal__timeline-sentinel" aria-hidden="true"></div>
      </div>

      <TgSkeleton v-else height="120px" />
    </TgCard>

    <TgModal :open="Boolean(selectedEvent)" title="Event detail" @close="closeEvent">
      <div v-if="selectedEvent" class="deal__event-detail">
        <p class="deal__event-detail-type">{{ selectedEvent.event_type }}</p>
        <p class="deal__event-detail-time">{{ formatTimelineTime(selectedEvent.created_at) }}</p>

        <p v-if="selectedEvent.event_type === 'message'" class="deal__event-message">
          {{ selectedMessageText || 'Message unavailable' }}
        </p>

        <div v-else-if="selectedEvent.event_type === 'proposal'" class="deal__event-proposal">
          <div v-if="selectedProposalMedia && !selectedProposalMediaError" class="deal__event-media">
            <img
              v-if="selectedProposalMedia.type === 'image'"
              class="deal__event-image"
              :src="selectedProposalMedia.src"
              alt="Proposal media"
              @error="onSelectedProposalMediaError"
            />
            <video
              v-else
              class="deal__event-video"
              :src="selectedProposalMedia.src"
              controls
              @error="onSelectedProposalMediaError"
            ></video>
          </div>
          <p v-if="selectedProposalMediaError" class="deal__event-note">Media preview unavailable.</p>

          <div v-for="row in selectedProposalRows" :key="row.key" class="deal__event-row">
            <span>{{ row.label }}</span>
            <strong>{{ row.value }}</strong>
          </div>
          <p v-if="selectedEvent !== latestProposalEvent" class="deal__event-note">
            Older proposal (read-only).
          </p>
        </div>
      </div>
    </TgModal>

    <TgModal :open="showEditModal" title="Edit proposal" max-width="520px" @close="closeEditModal">
      <div class="deal__edit-form">
        <label class="deal__field">
          <span>Creative text</span>
          <textarea
            v-model="editForm.creative_text"
            class="deal__textarea"
            rows="4"
            placeholder="Write your ad copy"
          ></textarea>
        </label>

        <TgInput v-model="editForm.start_at" label="Start at" type="datetime-local" />

        <label class="deal__field">
          <span>Media type</span>
          <select v-model="editForm.creative_media_type" class="deal__select">
            <option value="image">Image</option>
            <option value="video">Video</option>
          </select>
        </label>

        <label class="deal__upload">
          <span>Media file</span>
          <input
            type="file"
            :accept="editForm.creative_media_type === 'video' ? 'video/*' : 'image/*'"
            :disabled="uploadingEditMedia || actionLoading"
            @change="handleEditMediaFile"
          />
        </label>
        <TgBadge v-if="editMediaStatus" tone="success">{{ editMediaStatus }}</TgBadge>
        <p class="deal__media-note">If you do not upload new media, current media is kept.</p>
      </div>
      <template #footer>
        <TgButton
          full-width
          :loading="actionLoading || uploadingEditMedia"
          :disabled="!canSubmitEdit || uploadingEditMedia"
          @click="submitEdit"
        >
          Save proposal
        </TgButton>
      </template>
    </TgModal>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  TgBadge,
  TgButton,
  TgCard,
  TgInput,
  TgList,
  TgModal,
  TgSkeleton,
  TgStatePanel,
} from '../components/tg'
import { resolveRoleDefaultPath, isForbiddenMessage } from '../router/roleAccess'
import { dealsService } from '../services/deals'
import { useAuthStore } from '../stores/auth'
import type { DealDetail, DealTimelineEvent } from '../types/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const dealId = Number(route.params.id)
const deal = ref<DealDetail | null>(null)
const events = ref<DealTimelineEvent[]>([])
const nextCursor = ref<string | null>(null)
const loadingOlder = ref(false)
const actionLoading = ref(false)
const uploadingEditMedia = ref(false)
const editMediaStatus = ref('')
const error = ref('')
const selectedEvent = ref<DealTimelineEvent | null>(null)
const selectedProposalMediaError = ref(false)
const showEditModal = ref(false)
const timelineSentinel = ref<HTMLElement | null>(null)
let timelineObserver: IntersectionObserver | null = null

const editForm = reactive({
  creative_text: '',
  start_at: '',
  creative_media_type: 'image',
  creative_media_ref: '',
})

const DEFAULT_TIMELINE_LIMIT = 20
const NEGOTIATION_STATES = new Set(['DRAFT', 'NEGOTIATION'])
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

const role = computed(
  () => authStore.user?.preferred_role || (route.query.role as string | undefined),
)

const hasMoreEvents = computed(() => Boolean(nextCursor.value))

const latestProposalEvent = computed(() => events.value.find((event) => event.event_type === 'proposal') ?? null)

const isLatestProposalRecipient = computed(() => {
  const latest = latestProposalEvent.value
  const userId = authStore.user?.id
  if (!latest || userId == null || latest.actor_id == null) return false
  return latest.actor_id !== userId
})

const showNegotiationActions = computed(() => {
  if (!deal.value) return false
  return NEGOTIATION_STATES.has(deal.value.state) && isLatestProposalRecipient.value
})

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

const canSubmitEdit = computed(() => {
  return (
    showNegotiationActions.value &&
    editForm.creative_text.trim().length > 0 &&
    editForm.creative_media_ref.trim().length > 0 &&
    ['image', 'video'].includes(editForm.creative_media_type) &&
    !uploadingEditMedia.value
  )
})

const selectedMessageText = computed(() => {
  if (!selectedEvent.value || selectedEvent.value.event_type !== 'message') return ''
  const payload = toRecord(selectedEvent.value.payload)
  const text = payload?.text
  return typeof text === 'string' ? text : ''
})

const selectedProposalRows = computed(() => {
  if (!selectedEvent.value || selectedEvent.value.event_type !== 'proposal') {
    return [] as Array<{ key: string; label: string; value: string }>
  }
  const payload = toRecord(selectedEvent.value.payload)
  if (!payload) {
    return [] as Array<{ key: string; label: string; value: string }>
  }
  return proposalRows(payload)
})

const selectedProposalMedia = computed(() => {
  if (!selectedEvent.value || selectedEvent.value.event_type !== 'proposal') return null
  const payload = toRecord(selectedEvent.value.payload)
  if (!payload) return null

  const mediaRef = typeof payload.creative_media_ref === 'string' ? payload.creative_media_ref.trim() : ''
  if (!mediaRef) return null

  const mediaType = payload.creative_media_type === 'video' ? 'video' : 'image'
  return {
    type: mediaType,
    src: buildProposalMediaUrl(mediaRef),
  }
})

const botLink = computed(() => {
  const botUsername = import.meta.env.VITE_BOT_USERNAME || 'tgads_bot'
  return `https://t.me/${botUsername}?start=deal_${dealId}`
})

const formatTimelineTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  const now = new Date()
  const sameYear = date.getFullYear() === now.getFullYear()
  const sameDay =
    sameYear &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()

  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const month = MONTHS[date.getMonth()] ?? ''

  if (sameDay) {
    return `${hours}:${minutes}`
  }
  if (sameYear) {
    return `${day} ${month} ${hours}:${minutes}`
  }
  return `${day} ${month} ${date.getFullYear()}`
}

const toRecord = (payload: unknown): Record<string, unknown> | null => {
  if (!payload || Array.isArray(payload) || typeof payload !== 'object') return null
  return payload as Record<string, unknown>
}

const toDateTimeLocal = (value: unknown) => {
  if (typeof value !== 'string' || !value.trim()) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

const toIsoDateTime = (value: string): string | null => {
  const trimmed = value.trim()
  if (!trimmed) return null
  const parsed = new Date(trimmed)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed.toISOString()
}

const formatHumanDateTime = (value: string): string => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  const day = String(date.getDate()).padStart(2, '0')
  const month = MONTHS[date.getMonth()] ?? ''
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${day} ${month} ${year} ${hours}:${minutes}`
}

const getInitData = () => {
  if (typeof window === 'undefined') return null
  const tgInit = (window as typeof window & { Telegram?: { WebApp?: { initData?: string } } })
    .Telegram?.WebApp?.initData
  if (tgInit) return tgInit
  const params = new URLSearchParams(window.location.search)
  return params.get('initData')
}

const buildProposalMediaUrl = (mediaRef: string) => {
  const params = new URLSearchParams({ media_ref: mediaRef })
  const initData = getInitData()
  if (initData) {
    params.set('initData', initData)
  }
  return `${API_BASE}/deals/${dealId}/proposal/media?${params.toString()}`
}

const formatProposalValue = (key: string, value: unknown): string => {
  if (value == null) return '--'
  if (key === 'start_at' && typeof value === 'string') return formatHumanDateTime(value)
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value) || typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

const proposalRows = (payload: Record<string, unknown>) => {
  const labels: Record<string, string> = {
    price_ton: 'Price (TON)',
    ad_type: 'Ad type',
    placement_type: 'Placement type',
    exclusive_hours: 'Exclusive hours',
    retention_hours: 'Retention hours',
    creative_text: 'Creative text',
    creative_media_type: 'Media type',
    start_at: 'Start at',
    posting_params: 'Posting params',
  }

  const orderedKeys = [
    'price_ton',
    'ad_type',
    'placement_type',
    'exclusive_hours',
    'retention_hours',
    'creative_text',
    'creative_media_type',
    'start_at',
    'posting_params',
  ]

  return orderedKeys.map((key) => ({
    key,
    label: labels[key] ?? key,
    value: formatProposalValue(key, payload[key]),
  }))
}

const loadDeal = async () => {
  try {
    deal.value = await dealsService.get(dealId)
    const timeline = await dealsService.events(dealId, { limit: DEFAULT_TIMELINE_LIMIT })
    events.value = timeline.items
    nextCursor.value = timeline.next_cursor ?? null
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to load deal'
    if (isForbiddenMessage(message)) {
      await router.replace(resolveRoleDefaultPath(authStore.user?.preferred_role ?? null))
      return
    }
    error.value = message
  }
}

const loadOlderEvents = async () => {
  if (!nextCursor.value || loadingOlder.value) return
  loadingOlder.value = true
  try {
    const timeline = await dealsService.events(dealId, {
      cursor: nextCursor.value,
      limit: DEFAULT_TIMELINE_LIMIT,
    })
    events.value = [...events.value, ...timeline.items]
    nextCursor.value = timeline.next_cursor ?? null
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load older events'
  } finally {
    loadingOlder.value = false
  }
}

const setupTimelineObserver = () => {
  if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return
  timelineObserver?.disconnect()
  if (!timelineSentinel.value) return

  timelineObserver = new IntersectionObserver(
    (entries) => {
      if (!hasMoreEvents.value || loadingOlder.value) return
      if (entries.some((entry) => entry.isIntersecting)) {
        void loadOlderEvents()
      }
    },
    { rootMargin: '220px 0px' },
  )
  timelineObserver.observe(timelineSentinel.value)
}

const openEvent = (event: DealTimelineEvent) => {
  selectedEvent.value = event
  selectedProposalMediaError.value = false
}

const closeEvent = () => {
  selectedEvent.value = null
  selectedProposalMediaError.value = false
}

const openEditModal = () => {
  const proposalPayload = toRecord(latestProposalEvent.value?.payload) ?? {}
  editForm.creative_text =
    typeof proposalPayload.creative_text === 'string'
      ? proposalPayload.creative_text
      : (deal.value?.creative_text ?? '')

  const mediaType =
    typeof proposalPayload.creative_media_type === 'string'
      ? proposalPayload.creative_media_type
      : (deal.value?.creative_media_type ?? 'image')
  editForm.creative_media_type = mediaType === 'video' ? 'video' : 'image'

  editForm.creative_media_ref =
    typeof proposalPayload.creative_media_ref === 'string'
      ? proposalPayload.creative_media_ref
      : (deal.value?.creative_media_ref ?? '')

  editForm.start_at = toDateTimeLocal(
    typeof proposalPayload.start_at === 'string' ? proposalPayload.start_at : deal.value?.scheduled_at,
  )
  editMediaStatus.value = ''

  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editMediaStatus.value = ''
}

const handleEditMediaFile = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  const contentType = file.type || ''
  if (!contentType.startsWith('image/') && !contentType.startsWith('video/')) {
    error.value = 'Please select an image or video file.'
    return
  }

  uploadingEditMedia.value = true
  editMediaStatus.value = ''
  error.value = ''
  editForm.creative_media_ref = ''
  try {
    const response = await dealsService.uploadProposalMedia(dealId, file)
    editForm.creative_media_ref = response.creative_media_ref
    editForm.creative_media_type = response.creative_media_type === 'video' ? 'video' : 'image'
    editMediaStatus.value = 'Uploaded to Telegram'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to upload media'
  } finally {
    uploadingEditMedia.value = false
    ;(event.target as HTMLInputElement).value = ''
  }
}

const onSelectedProposalMediaError = () => {
  selectedProposalMediaError.value = true
}

const submitEdit = async () => {
  if (!canSubmitEdit.value || uploadingEditMedia.value) return

  actionLoading.value = true
  error.value = ''
  try {
    await dealsService.update(dealId, {
      creative_text: editForm.creative_text.trim(),
      start_at: toIsoDateTime(editForm.start_at),
      creative_media_type: editForm.creative_media_type,
      creative_media_ref: editForm.creative_media_ref.trim(),
    })
    closeEditModal()
    await loadDeal()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to edit proposal'
  } finally {
    actionLoading.value = false
  }
}

const approveProposal = async () => {
  actionLoading.value = true
  error.value = ''
  try {
    await dealsService.accept(dealId)
    await loadDeal()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to approve proposal'
  } finally {
    actionLoading.value = false
  }
}

const rejectProposal = async () => {
  if (!window.confirm('Reject this deal proposal? This will close the negotiation.')) {
    return
  }

  actionLoading.value = true
  error.value = ''
  try {
    await dealsService.reject(dealId)
    await loadDeal()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to reject proposal'
  } finally {
    actionLoading.value = false
  }
}

const navigateAction = () => {
  if (actionLink.value) {
    void router.push(actionLink.value)
  }
}

watch(timelineSentinel, () => {
  setupTimelineObserver()
})

onMounted(() => {
  const initialize = async () => {
    if (!authStore.bootstrapped) {
      await authStore.bootstrap()
    }
    await loadDeal()
    setupTimelineObserver()
  }
  void initialize()
})

onBeforeUnmount(() => {
  timelineObserver?.disconnect()
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
  width: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--app-ink-muted);
  text-align: left;
}

.deal__event time {
  white-space: nowrap;
  text-align: right;
  margin-left: 1rem;
  color: var(--app-ink-muted);
  font-weight: 600;
}

.deal__timeline-status {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.85rem;
  text-align: center;
}

.deal__timeline-sentinel {
  height: 1px;
}

.deal__actions {
  display: grid;
  gap: 0.75rem;
}

.deal__proposal-actions {
  display: grid;
  gap: 0.65rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.deal__action-btn {
  justify-content: center;
}

.deal__action-btn--edit {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  border: 1px solid transparent !important;
  color: #fff !important;
}

.deal__action-btn--approve {
  background: linear-gradient(135deg, #16a34a, #15803d) !important;
  border: 1px solid transparent !important;
  color: #fff !important;
}

.deal__action-btn--reject {
  background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
  border: 1px solid transparent !important;
  color: #fff !important;
}

.deal__bot {
  font-weight: 600;
  color: var(--app-accent);
  text-align: center;
}

.deal__event-detail {
  display: grid;
  gap: 0.75rem;
  max-height: min(70vh, 560px);
  overflow-y: auto;
  padding-right: 0.2rem;
}

.deal__event-detail-type {
  margin: 0;
  font-weight: 700;
}

.deal__event-detail-time {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.85rem;
}

.deal__event-message {
  margin: 0;
  white-space: pre-wrap;
}

.deal__event-proposal {
  display: grid;
  gap: 0.45rem;
}

.deal__event-media {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  overflow: hidden;
  background: #111;
}

.deal__event-image,
.deal__event-video {
  width: 100%;
  max-height: 280px;
  object-fit: contain;
  display: block;
}

.deal__event-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.deal__event-row span {
  color: var(--app-ink-muted);
}

.deal__event-row strong {
  text-align: right;
  max-width: 70%;
  word-break: break-word;
}

.deal__event-note {
  margin: 0.2rem 0 0;
  color: var(--app-ink-muted);
  font-size: 0.82rem;
}

.deal__edit-form {
  display: grid;
  gap: 0.75rem;
}

.deal__field {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.deal__field > span {
  color: var(--app-ink-muted);
  font-weight: 600;
}

.deal__textarea {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  font-family: inherit;
  background: var(--app-surface);
  color: var(--app-ink);
  resize: vertical;
  min-height: 110px;
}

.deal__select {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  background: var(--app-surface);
  color: var(--app-ink);
}

.deal__upload {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.deal__upload > span {
  color: var(--app-ink-muted);
  font-weight: 600;
}

.deal__upload input {
  border-radius: var(--app-radius-md);
  border: 1px dashed rgba(25, 25, 25, 0.25);
  padding: 0.65rem;
  background: var(--app-surface);
}

.deal__media-note {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.82rem;
}

@media (max-width: 520px) {
  .deal__action-btn {
    font-size: 0.82rem;
    padding: 0.6rem 0.35rem;
  }
}
</style>
