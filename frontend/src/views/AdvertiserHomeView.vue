<template>
  <section class="home">
    <TgCard title="Advertiser hub" subtitle="Discover channels and manage campaigns.">
      <div class="home__actions">
        <RouterLink class="home__link" to="/advertiser/marketplace">Browse marketplace</RouterLink>
        <RouterLink class="home__link" to="/advertiser/campaigns/new"
          >Create campaign request</RouterLink
        >
        <RouterLink class="home__link" to="/advertiser/offers">Review offers</RouterLink>
        <RouterLink class="home__link" to="/advertiser/deals">View deals inbox</RouterLink>
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

import { TgCard } from '../components/tg'
</script>

<style scoped>
.home__actions {
  display: grid;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.home__link {
  font-weight: 600;
  color: var(--app-accent);
}
</style>
