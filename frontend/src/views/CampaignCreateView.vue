<template>
  <section class="campaign">
    <TgCard title="Create campaign" subtitle="TON-only budget for M11.">
      <TgStatePanel v-if="error" title="Couldn't create campaign" :description="error">
        <template #icon>!</template>
      </TgStatePanel>

      <div class="campaign__form">
        <TgInput v-model="form.title" label="Title" placeholder="Spring launch" />
        <TgInput v-model="form.brief" label="Brief" placeholder="What should owners know?" />
        <TgInput v-model="form.budget_ton" label="Budget (TON)" type="number" />
        <TgInput v-model="form.min_subscribers" label="Min subscribers" type="number" />
        <TgInput v-model="form.min_avg_views" label="Min avg views" type="number" />
        <TgButton full-width :loading="loading" @click="submit">Create campaign</TgButton>
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'

import { TgButton, TgCard, TgInput, TgStatePanel } from '../components/tg'
import { campaignsService } from '../services/campaigns'

const loading = ref(false)
const error = ref('')

const form = reactive({
  title: '',
  brief: '',
  budget_ton: '',
  min_subscribers: '',
  min_avg_views: '',
})

const submit = async () => {
  if (!form.title.trim() || !form.brief.trim() || !form.budget_ton.trim()) {
    error.value = 'Title, brief, and TON budget are required.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await campaignsService.create({
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
    error.value = err instanceof Error ? err.message : 'Failed to create campaign'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.campaign__form {
  display: grid;
  gap: 0.85rem;
}
</style>
