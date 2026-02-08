<template>
  <section class="verify">
    <TgCard title="Verify channel" subtitle="Grant admin rights, then verify your channel.">
      <div class="verify__content">
        <TgStatePanel
          v-if="channelsStore.error"
          title="Permission issue"
          :description="channelsStore.error"
        >
          <template #icon>🔒</template>
        </TgStatePanel>
        <TgStatePanel
          v-else
          title="Ready to verify"
          description="Add both accounts below as channel admins before pressing verify."
        >
          <template #icon>✅</template>
        </TgStatePanel>
        <div class="verify__requirements">
          <p class="verify__requirements-title">Required admin accounts</p>
          <ul class="verify__requirements-list">
            <li>
              Bot account:
              <strong>@{{ botUsername }}</strong>
            </li>
            <li v-if="verifyUserUsername">
              Verification user:
              <strong>@{{ verifyUserUsername }}</strong>
            </li>
            <li v-else>
              Verification user:
              <strong>Not configured</strong>
            </li>
          </ul>
        </div>
        <TgButton full-width :loading="channelsStore.loading" @click="handleVerify"
          >Verify now</TgButton
        >
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { TgButton, TgCard, TgStatePanel } from '../components/tg'
import { useChannelsStore } from '../stores/channels'

const route = useRoute()
const router = useRouter()
const channelsStore = useChannelsStore()

const channelId = computed(() => Number(route.params.id))
const botUsername = normalizeUsername(import.meta.env.VITE_BOT_USERNAME || 'tgads_bot')
const verifyUserUsername = normalizeUsername(import.meta.env.VITE_TELEGRAM_VERIFY_USER_USERNAME || '')
const activeChannel = computed(() =>
  channelsStore.items.find((item) => item.id === channelId.value),
)
const isChannelVerified = computed(() => Boolean(activeChannel.value?.is_verified))

const handleVerify = async () => {
  if (!channelId.value) return
  if (isChannelVerified.value) {
    await goToListing()
    return
  }

  await channelsStore.verifyChannel(channelId.value)
  if (channelsStore.error) return

  void channelsStore.fetchChannels()
  await goToListing()
}

function normalizeUsername(raw: string): string {
  const value = raw.trim()
  if (!value) return ''
  return value.startsWith('@') ? value.slice(1) : value
}

async function goToListing() {
  if (!channelId.value) return
  await router.replace(`/owner/channels/${channelId.value}/listing`)
}

onMounted(async () => {
  if (!channelId.value) return
  if (!channelsStore.items.length) {
    await channelsStore.fetchChannels()
  }
  if (isChannelVerified.value) {
    await goToListing()
  }
})
</script>

<style scoped>
.verify__content {
  display: grid;
  gap: 1rem;
}

.verify__requirements {
  padding: 0.85rem 1rem;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  background: var(--app-surface);
}

.verify__requirements-title {
  margin: 0 0 0.4rem 0;
  font-weight: 600;
}

.verify__requirements-list {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--app-ink-muted);
}
</style>
