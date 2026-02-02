<template>
  <section class="landing">
    <TgCard title="Choose your role" subtitle="You can change this later in Profile.">
      <div class="landing__actions">
        <TgButton full-width>I'm a Channel Owner</TgButton>
        <TgButton variant="secondary" full-width>I'm an Advertiser</TgButton>
      </div>
    </TgCard>
    <TgStatePanel
      title="Telegram-native experience"
      description="This mini app mirrors Telegram style tokens and keeps everything inside your chat flow."
    >
      <template #icon>✦</template>
    </TgStatePanel>
  </section>
</template>

<script setup lang="ts">
import { TgButton, TgCard, TgStatePanel } from '../components/tg'
</script>

<style scoped>
.landing {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.landing__actions {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}
</style>
