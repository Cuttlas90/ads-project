<template>
  <TgAppLayout>
    <template #title>Telegram Ads</template>
    <template #actions>
      <span class="app-role">M11</span>
    </template>

    <router-view />

    <template #nav>
      <RouterLink class="nav-link" to="/">Home</RouterLink>
      <RouterLink class="nav-link" to="/owner">Owner</RouterLink>
      <RouterLink class="nav-link" to="/advertiser">Advertiser</RouterLink>
    </template>
  </TgAppLayout>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

import TgAppLayout from './layouts/TgAppLayout.vue'
</script>

<style scoped>
.app-role {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--app-ink-muted);
}

.nav-link {
  font-weight: 600;
  color: var(--app-ink-muted);
}

.nav-link.router-link-active {
  color: var(--app-accent);
}
</style>
