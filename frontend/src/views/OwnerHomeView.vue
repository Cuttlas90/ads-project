<template>
  <section class="home">
    <TgCard title="Owner dashboard" subtitle="Channels, listings, and active deals at a glance.">
      <div class="home__meta">
        <TgBadge tone="success">Verified Ready</TgBadge>
        <TgBadge tone="warning">Draft listings</TgBadge>
      </div>
      <RouterLink class="verify-link" to="/owner/campaigns">Browse campaigns</RouterLink>
      <RouterLink class="verify-link" to="/owner/deals">View deals inbox</RouterLink>
      <div class="home__add">
        <TgInput v-model="newChannel" placeholder="@yourchannel" label="Add a channel" />
        <TgButton full-width :loading="channelsStore.loading" @click="handleAdd">Submit</TgButton>
      </div>
      <TgStatePanel
        v-if="channelsStore.error"
        title="Couldn't load channels"
        :description="channelsStore.error"
      >
        <template #icon>!</template>
      </TgStatePanel>
      <div v-else class="home__list">
        <TgSkeleton v-if="channelsStore.loading && !channelsStore.items.length" height="64px" />
        <TgStatePanel
          v-else-if="!channelsStore.items.length"
          title="No channels yet"
          description="Add your first channel to start listing ad formats."
        />
        <TgCard
          v-for="channel in channelsStore.items"
          :key="channel.id"
          :title="channel.title || channel.username || 'Channel'"
        >
          <div class="home__row">
            <span>@{{ channel.username }}</span>
            <TgBadge :tone="channel.is_verified ? 'success' : 'warning'">
              {{ channel.is_verified ? 'Verified' : 'Needs verify' }}
            </TgBadge>
          </div>
          <div class="home__links">
            <RouterLink
              v-if="!channel.is_verified"
              class="verify-link"
              :to="`/owner/channels/${channel.id}/verify`"
            >
              Verify channel
            </RouterLink>
            <RouterLink class="verify-link" :to="`/owner/channels/${channel.id}/listing`">
              Edit listing
            </RouterLink>
          </div>
        </TgCard>
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { RouterLink } from 'vue-router'

import { TgBadge, TgButton, TgCard, TgInput, TgSkeleton, TgStatePanel } from '../components/tg'
import { useChannelsStore } from '../stores/channels'

const channelsStore = useChannelsStore()
const newChannel = ref('')

const handleAdd = async () => {
  if (!newChannel.value.trim()) return
  await channelsStore.addChannel(newChannel.value.trim())
  newChannel.value = ''
}

onMounted(() => {
  void channelsStore.fetchChannels()
})
</script>

<style scoped>
.home__meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}

.home__add {
  display: grid;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.home__list {
  display: grid;
  gap: 0.75rem;
}

.home__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
  color: var(--app-ink-muted);
}

.verify-link {
  display: inline-block;
  margin-top: 0.65rem;
  font-weight: 600;
  color: var(--app-accent);
}

.home__links {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}
</style>
