<template>
  <section class="owner-campaigns">
    <TgCard title="Campaigns" subtitle="Browse active campaigns and apply from verified channels.">
      <div class="owner-campaigns__filters-toggle">
        <TgButton
          size="sm"
          variant="ghost"
          :aria-expanded="(!filtersCollapsed).toString()"
          aria-controls="owner-campaigns-filters"
          @click="filtersCollapsed = !filtersCollapsed"
        >
          {{ filtersCollapsed ? 'Show filters' : 'Hide filters' }}
        </TgButton>
      </div>

      <div v-if="!filtersCollapsed" id="owner-campaigns-filters" class="owner-campaigns__filters">
        <TgInput
          v-model="search"
          label="Search"
          placeholder="Title or brief"
          @keyup.enter="loadCampaigns"
        />
        <div class="owner-campaigns__filter-row">
          <TgInput
            v-model="minBudgetTon"
            label="Min budget (TON)"
            placeholder="e.g. 5"
            type="number"
          />
          <TgInput
            v-model="maxBudgetTon"
            label="Max budget (TON)"
            placeholder="e.g. 50"
            type="number"
          />
        </div>
        <!-- <TgInput
          v-model="preferredLanguage"
          label="Preferred language"
          placeholder="e.g. en"
        /> -->
        <div class="owner-campaigns__filter-row">
          <TgInput
            v-model="maxRequiredSubscribers"
            label="Max required subscribers"
            placeholder="e.g. 50000"
            type="number"
          />
          <!-- <TgInput
            v-model="maxRequiredAvgViews"
            label="Max required avg views"
            placeholder="e.g. 5000"
            type="number"
          /> -->
        </div>
        <TgButton full-width :loading="campaignsStore.loadingDiscover" @click="loadCampaigns">
          Apply filters
        </TgButton>
      </div>

      <TgStatePanel v-if="campaignsStore.error" title="Couldn't load campaigns" :description="campaignsStore.error">
        <template #icon>!</template>
      </TgStatePanel>

      <TgStatePanel
        v-if="!verifiedChannels.length"
        title="No verified channels"
        description="Verify at least one channel before applying to campaigns."
      >
        <template #icon>i</template>
      </TgStatePanel>

      <div v-if="discoverItems.length" class="owner-campaigns__list">
        <TgCard
          v-for="campaign in discoverItems"
          :key="campaign.id"
          :title="campaign.title"
        >
        <!-- <TgCard
          v-for="campaign in discoverItems"
          :key="campaign.id"
          :title="campaign.title"
          :subtitle="`Max accepts: ${campaign.max_acceptances}`"
        > -->
          <p class="owner-campaigns__brief">{{ campaign.brief }}</p>
          <p class="owner-campaigns__meta">
            Budget: {{ campaign.budget_ton ?? '--' }} TON · Min subs: {{ campaign.min_subscribers ?? '--' }}
          </p>

          <div class="owner-campaigns__apply">
            <label class="owner-campaigns__field">
              <span>Verified channel</span>
              <select v-model.number="formFor(campaign.id).channelId" class="owner-campaigns__select">
                <option :value="0" disabled>Select channel</option>
                <option v-for="channel in verifiedChannels" :key="channel.id" :value="channel.id">
                  {{ channel.title || channel.username || `Channel ${channel.id}` }}
                </option>
              </select>
            </label>
            <label class="owner-campaigns__field">
              <span>Placement type</span>
              <select v-model="formFor(campaign.id).placementType" class="owner-campaigns__select">
                <option value="post">Post</option>
                <option value="story">Story</option>
              </select>
            </label>
            <div class="owner-campaigns__terms">
              <TgInput
                v-model="formFor(campaign.id).exclusiveHours"
                label="Exclusive hours"
                type="number"
              />
              <TgInput
                v-model="formFor(campaign.id).retentionHours"
                label="Retention hours"
                type="number"
              />
            </div>
            <TgInput
              v-model="formFor(campaign.id).message"
              label="Message (optional)"
              placeholder="Short note for advertiser"
            />
            <TgButton
              full-width
              :disabled="!verifiedChannels.length"
              :loading="campaignsStore.applying && applyingCampaignId === campaign.id"
              @click="apply(campaign.id)"
            >
              Apply
            </TgButton>
            <TgBadge v-if="successByCampaign[campaign.id]" tone="success">
              {{ successByCampaign[campaign.id] }}
            </TgBadge>
          </div>
        </TgCard>
      </div>

      <TgStatePanel
        v-else-if="!campaignsStore.loadingDiscover && !campaignsStore.error"
        title="No campaigns found"
        description="Try different filters or check back soon."
      />
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { TgBadge, TgButton, TgCard, TgInput, TgStatePanel } from '../components/tg'
import { useCampaignsStore } from '../stores/campaigns'
import { useChannelsStore } from '../stores/channels'

interface ApplyForm {
  channelId: number
  placementType: 'post' | 'story'
  exclusiveHours: string
  retentionHours: string
  message: string
}

const campaignsStore = useCampaignsStore()
const channelsStore = useChannelsStore()

const filtersCollapsed = ref(true)
const search = ref('')
const minBudgetTon = ref('')
const maxBudgetTon = ref('')
const preferredLanguage = ref('')
const maxRequiredSubscribers = ref('')
const maxRequiredAvgViews = ref('')
const applyingCampaignId = ref<number | null>(null)
const forms = reactive<Record<number, ApplyForm>>({})
const successByCampaign = reactive<Record<number, string>>({})

const rawDiscoverItems = computed(() => campaignsStore.discoverPage?.items ?? [])
const verifiedChannels = computed(() => channelsStore.items.filter((channel) => channel.is_verified))

const toNumber = (value: string): number | null => {
  const trimmed = value.trim()
  if (!trimmed) return null
  const parsed = Number(trimmed)
  if (!Number.isFinite(parsed)) return null
  return parsed
}

const toCampaignBudgetTon = (value: string | null | undefined): number | null => {
  if (!value) return null
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return null
  return parsed
}

const discoverItems = computed(() => {
  const minBudget = toNumber(minBudgetTon.value)
  const maxBudget = toNumber(maxBudgetTon.value)
  const language = preferredLanguage.value.trim().toLowerCase()
  const maxSubscribers = toNumber(maxRequiredSubscribers.value)
  const maxAvgViews = toNumber(maxRequiredAvgViews.value)

  return rawDiscoverItems.value.filter((campaign) => {
    const budget = toCampaignBudgetTon(campaign.budget_ton)
    if (minBudget !== null && (budget === null || budget < minBudget)) {
      return false
    }
    if (maxBudget !== null && (budget === null || budget > maxBudget)) {
      return false
    }

    if (language) {
      const campaignLanguage = (campaign.preferred_language ?? '').toLowerCase()
      if (!campaignLanguage.includes(language)) {
        return false
      }
    }

    if (
      maxSubscribers !== null &&
      campaign.min_subscribers !== null &&
      campaign.min_subscribers !== undefined &&
      campaign.min_subscribers > maxSubscribers
    ) {
      return false
    }

    if (
      maxAvgViews !== null &&
      campaign.min_avg_views !== null &&
      campaign.min_avg_views !== undefined &&
      campaign.min_avg_views > maxAvgViews
    ) {
      return false
    }

    return true
  })
})

const formFor = (campaignId: number): ApplyForm => {
  if (!forms[campaignId]) {
    forms[campaignId] = {
      channelId: 0,
      placementType: 'post',
      exclusiveHours: '0',
      retentionHours: '24',
      message: '',
    }
  }
  return forms[campaignId]
}

const loadCampaigns = async () => {
  await campaignsStore.fetchDiscoverCampaigns({ search: search.value.trim() || undefined })
}

const apply = async (campaignId: number) => {
  const form = formFor(campaignId)
  const exclusiveHours = Number(form.exclusiveHours)
  const retentionHours = Number(form.retentionHours)
  if (!form.channelId) {
    campaignsStore.error = 'Verified channel is required.'
    return
  }
  if (
    Number.isNaN(exclusiveHours) ||
    !Number.isInteger(exclusiveHours) ||
    exclusiveHours < 0 ||
    Number.isNaN(retentionHours) ||
    !Number.isInteger(retentionHours) ||
    retentionHours < 1
  ) {
    campaignsStore.error = 'Exclusive must be >= 0 and retention must be >= 1.'
    return
  }
  applyingCampaignId.value = campaignId
  successByCampaign[campaignId] = ''
  try {
    await campaignsStore.applyToCampaign(campaignId, {
      channel_id: form.channelId,
      proposed_format_label: form.placementType === 'story' ? 'Story' : 'Post',
      proposed_placement_type: form.placementType,
      proposed_exclusive_hours: exclusiveHours,
      proposed_retention_hours: retentionHours,
      message: form.message.trim() || undefined,
    })
    successByCampaign[campaignId] = 'Application sent'
  } finally {
    applyingCampaignId.value = null
  }
}

onMounted(async () => {
  await Promise.all([loadCampaigns(), channelsStore.fetchChannels()])
})
</script>

<style scoped>
.owner-campaigns__filters-toggle {
  display: flex;
  margin-bottom: 0.75rem;
}

.owner-campaigns__filters {
  display: grid;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.owner-campaigns__filter-row {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
}

.owner-campaigns__list {
  display: grid;
  gap: 0.85rem;
}

.owner-campaigns__brief {
  margin: 0 0 0.5rem;
  color: var(--app-ink);
}

.owner-campaigns__meta {
  margin: 0 0 0.85rem;
  color: var(--app-ink-muted);
  font-size: 0.85rem;
}

.owner-campaigns__apply {
  display: grid;
  gap: 0.65rem;
}

.owner-campaigns__terms {
  display: grid;
  gap: 0.65rem;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
}

.owner-campaigns__field {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.owner-campaigns__field > span {
  color: var(--app-ink-muted);
  font-weight: 600;
}

.owner-campaigns__select {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  background: var(--app-surface);
  color: var(--app-ink);
}
</style>
