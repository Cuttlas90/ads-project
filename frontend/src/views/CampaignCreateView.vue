<template>
  <section class="campaign">
    <TgCard title="Create campaign" subtitle="TON-only budget for M11.">
      <TgStatePanel v-if="campaignsStore.error" title="Couldn't process campaign" :description="campaignsStore.error">
        <template #icon>!</template>
      </TgStatePanel>

      <div class="campaign__form">
        <TgInput v-model="form.title" label="Title" placeholder="Spring launch" />
        <TgInput v-model="form.brief" label="Brief" placeholder="What should owners know?" />
        <TgInput v-model="form.budget_ton" label="Budget (TON)" type="number" />
        <TgInput v-model="form.min_subscribers" label="Min subscribers" type="number" />
        <TgInput v-model="form.min_avg_views" label="Min avg views" type="number" />
        <TgButton full-width :loading="campaignsStore.creating" @click="submit">Create campaign</TgButton>
      </div>
      <div class="campaign__list">
        <TgSkeleton v-if="campaignsStore.loadingAdvertiser && !campaignItems.length" height="84px" />
        <TgStatePanel
          v-else-if="!campaignItems.length"
          title="No campaigns yet"
          description="Create your first campaign to collect owner offers."
        />
        <TgCard v-for="campaign in campaignItems" :key="campaign.id" :title="campaign.title">
          <p class="campaign__brief">{{ campaign.brief }}</p>
          <p class="campaign__meta">
            Budget: {{ campaign.budget_ton ?? '--' }} TON · State: {{ campaign.lifecycle_state }}
          </p>
          <div class="campaign__actions">
            <RouterLink class="campaign__link" :to="`/advertiser/offers?campaign_id=${campaign.id}`">
              View offers
            </RouterLink>
            <TgButton
              size="sm"
              variant="secondary"
              :loading="campaignsStore.deleting && deletingCampaignId === campaign.id"
              @click="confirmDelete(campaign.id)"
            >
              Delete campaign
            </TgButton>
          </div>
        </TgCard>
      </div>
    </TgCard>

    <TgModal :open="deleteModalOpen" title="Delete campaign" @close="closeDeleteModal">
      <p class="campaign__delete-copy">
        Deleting will hide this campaign and related offers from campaign pages. Accepted deals remain
        available in deal history and deal detail.
      </p>
      <template #footer>
        <div class="campaign__delete-actions">
          <TgButton variant="secondary" @click="closeDeleteModal">Cancel</TgButton>
          <TgButton :loading="campaignsStore.deleting" @click="deleteCampaign">Delete campaign</TgButton>
        </div>
      </template>
    </TgModal>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { TgButton, TgCard, TgInput, TgModal, TgSkeleton, TgStatePanel } from '../components/tg'
import { useCampaignsStore } from '../stores/campaigns'

const campaignsStore = useCampaignsStore()
const deletingCampaignId = ref<number | null>(null)
const deleteModalOpen = ref(false)
const campaignToDelete = ref<number | null>(null)

const campaignItems = computed(() => campaignsStore.advertiserPage?.items ?? [])

const form = reactive({
  title: '',
  brief: '',
  budget_ton: '',
  min_subscribers: '',
  min_avg_views: '',
})

const submit = async () => {
  if (!form.title.trim() || !form.brief.trim() || !form.budget_ton.trim()) {
    campaignsStore.error = 'Title, brief, and TON budget are required.'
    return
  }
  try {
    await campaignsStore.createCampaign({
      title: form.title.trim(),
      brief: form.brief.trim(),
      budget_ton: Number(form.budget_ton),
      min_subscribers: form.min_subscribers ? Number(form.min_subscribers) : undefined,
      min_avg_views: form.min_avg_views ? Number(form.min_avg_views) : undefined,
    })
    form.title = ''
    form.brief = ''
    form.budget_ton = ''
    form.min_subscribers = ''
    form.min_avg_views = ''
  } catch (err) {
    campaignsStore.error = err instanceof Error ? err.message : 'Failed to create campaign'
  }
}

const confirmDelete = (campaignId: number) => {
  campaignToDelete.value = campaignId
  deleteModalOpen.value = true
}

const closeDeleteModal = () => {
  deleteModalOpen.value = false
  campaignToDelete.value = null
}

const deleteCampaign = async () => {
  if (!campaignToDelete.value) return
  deletingCampaignId.value = campaignToDelete.value
  try {
    await campaignsStore.deleteCampaign(campaignToDelete.value)
    closeDeleteModal()
  } finally {
    deletingCampaignId.value = null
  }
}

onMounted(() => {
  void campaignsStore.fetchAdvertiserCampaigns()
})
</script>

<style scoped>
.campaign__form {
  display: grid;
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.campaign__list {
  display: grid;
  gap: 0.75rem;
}

.campaign__brief {
  margin: 0 0 0.4rem;
  color: var(--app-ink);
}

.campaign__meta {
  margin: 0 0 0.75rem;
  color: var(--app-ink-muted);
  font-size: 0.85rem;
}

.campaign__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.campaign__link {
  font-weight: 600;
  color: var(--app-accent);
}

.campaign__delete-copy {
  margin: 0;
  color: var(--app-ink-muted);
}

.campaign__delete-actions {
  display: grid;
  gap: 0.5rem;
}
</style>
