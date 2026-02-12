<template>
  <TgAppLayout>
    <template #title>Telegram Ads</template>
    <template #actions>
      <span class="app-role">{{ roleLabel }}</span>
    </template>
    <template #top-notifications>
      <TgToastStack />
    </template>

    <router-view v-if="authStore.bootstrapped" />
    <TgSkeleton v-else height="120px" />

    <template v-if="authStore.bootstrapped" #nav>
      <RouterLink v-for="link in navLinks" :key="link.to" class="nav-link" :to="link.to">
        {{ link.label }}
      </RouterLink>
    </template>
  </TgAppLayout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import { TgSkeleton, TgToastStack } from './components/tg'
import TgAppLayout from './layouts/TgAppLayout.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()

const navConfig = {
  null: [{ to: '/profile', label: 'Profile' }],
  owner: [
    { to: '/owner', label: 'Owner' },
    { to: '/owner/campaigns', label: 'Campaigns' },
    { to: '/owner/deals', label: 'Deals' },
    { to: '/profile', label: 'Profile' },
  ],
  advertiser: [
    { to: '/advertiser/marketplace', label: 'Marketplace' },
    { to: '/advertiser/campaigns/new', label: 'Campaign' },
    { to: '/advertiser/offers', label: 'Offers' },
    { to: '/advertiser/deals', label: 'Deals' },
    { to: '/profile', label: 'Profile' },
  ],
} as const

const activeRole = computed(() => authStore.user?.preferred_role ?? null)
const navLinks = computed(() => {
  if (activeRole.value === 'owner') {
    return navConfig.owner
  }
  if (activeRole.value === 'advertiser') {
    return navConfig.advertiser
  }
  return navConfig.null
})

const roleLabel = computed(() => {
  if (activeRole.value === 'owner') {
    return 'OWNER'
  }
  if (activeRole.value === 'advertiser') {
    return 'ADVERTISER'
  }
  return 'PROFILE'
})
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
