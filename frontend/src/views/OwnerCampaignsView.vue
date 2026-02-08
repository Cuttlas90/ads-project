<template>
  <section class="owner-campaigns">
    <TgCard title="Campaigns" subtitle="Browse active campaigns and apply from verified channels.">
      <div class="owner-campaigns__search">
        <TgInput
          v-model="search"
          label="Search"
          placeholder="Title or brief"
          @keyup.enter="loadCampaigns"
        />
        <TgButton full-width :loading="campaignsStore.loadingDiscover" @click="loadCampaigns">
          Search
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
          :subtitle="`Max accepts: ${campaign.max_acceptances}`"
        >
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
            <TgInput
              v-model="formFor(campaign.id).proposedFormat"
              label="Proposed format"
              placeholder="Post"
            />
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
        description="Try a different search or check back soon."
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
  proposedFormat: string
  message: string
}

const campaignsStore = useCampaignsStore()
const channelsStore = useChannelsStore()

const search = ref('')
const applyingCampaignId = ref<number | null>(null)
const forms = reactive<Record<number, ApplyForm>>({})
const successByCampaign = reactive<Record<number, string>>({})

const discoverItems = computed(() => campaignsStore.discoverPage?.items ?? [])
const verifiedChannels = computed(() => channelsStore.items.filter((channel) => channel.is_verified))

const formFor = (campaignId: number): ApplyForm => {
  if (!forms[campaignId]) {
    forms[campaignId] = {
      channelId: 0,
      proposedFormat: 'Post',
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
  if (!form.channelId || !form.proposedFormat.trim()) {
    campaignsStore.error = 'Verified channel and proposed format are required.'
    return
  }
  applyingCampaignId.value = campaignId
  successByCampaign[campaignId] = ''
  try {
    await campaignsStore.applyToCampaign(campaignId, {
      channel_id: form.channelId,
      proposed_format_label: form.proposedFormat.trim(),
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
.owner-campaigns__search {
  display: grid;
  gap: 0.75rem;
  margin-bottom: 1rem;
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
