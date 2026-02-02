<template>
  <section class="verify">
    <TgCard title="Verify channel" subtitle="Grant bot permissions, then verify your channel.">
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
          description="Make sure the bot is an admin with posting rights."
        >
          <template #icon>✅</template>
        </TgStatePanel>
        <TgButton full-width :loading="channelsStore.loading" @click="handleVerify"
          >Verify now</TgButton
        >
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { TgButton, TgCard, TgStatePanel } from '../components/tg'
import { useChannelsStore } from '../stores/channels'

const route = useRoute()
const channelsStore = useChannelsStore()

const channelId = computed(() => Number(route.params.id))

const handleVerify = async () => {
  if (!channelId.value) return
  await channelsStore.verifyChannel(channelId.value)
}
</script>

<style scoped>
.verify__content {
  display: grid;
  gap: 1rem;
}
</style>
