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
        <span class="nav-link__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path :d="navIconPaths[link.icon]" />
          </svg>
        </span>
        <span class="nav-link__label">{{ link.label }}</span>
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

type NavIcon = 'home' | 'campaigns' | 'deals' | 'profile' | 'marketplace' | 'offers' | 'compose'
type NavLink = { to: string; label: string; icon: NavIcon }

const navIconPaths: Record<NavIcon, string> = {
  home: 'M3.75 9.75 12 3l8.25 6.75M6.75 9.75V20.25H17.25V9.75',
  campaigns: 'M4.5 12h3.75l8.25-3.75v7.5L8.25 12H4.5zM8.25 12v5.25a1.5 1.5 0 0 0 1.5 1.5h.75',
  deals: 'M3.75 12h4.5l2.25-2.25 3.75 3.75 2.25-2.25h3.75M3.75 12v6h16.5v-6',
  profile: 'M12 12a3.75 3.75 0 1 0 0-7.5 3.75 3.75 0 0 0 0 7.5zm-6.75 7.5a6.75 6.75 0 0 1 13.5 0',
  marketplace:
    'M12 3.75 19.5 6.75 20.25 12 17.25 19.5 12 20.25 6.75 17.25 3.75 12 6.75 6.75zM10.5 10.5l4.5-1.5-1.5 4.5-4.5 1.5z',
  offers:
    'M12 4.5a4.5 4.5 0 0 1 4.5 4.5v2.25c0 1.2.45 2.36 1.28 3.23l.47.52H5.75l.47-.52A4.73 4.73 0 0 0 7.5 11.25V9A4.5 4.5 0 0 1 12 4.5zm-2.25 10.5a2.25 2.25 0 0 0 4.5 0',
  compose: 'm7.5 16.5-1.5 4.5 4.5-1.5 8.25-8.25-3-3zM13.5 4.5l3 3',
}

const navConfig: Record<'null' | 'owner' | 'advertiser', readonly NavLink[]> = {
  null: [{ to: '/profile', label: 'Profile', icon: 'profile' }],
  owner: [
    { to: '/owner', label: 'Owner', icon: 'home' },
    { to: '/owner/campaigns', label: 'Campaigns', icon: 'campaigns' },
    { to: '/owner/deals', label: 'Deals', icon: 'deals' },
    { to: '/profile', label: 'Profile', icon: 'profile' },
  ],
  advertiser: [
    { to: '/advertiser/marketplace', label: 'Marketplace', icon: 'marketplace' },
    { to: '/advertiser/campaigns/new', label: 'Campaign', icon: 'compose' },
    { to: '/advertiser/offers', label: 'Offers', icon: 'offers' },
    { to: '/advertiser/deals', label: 'Deals', icon: 'deals' },
    { to: '/profile', label: 'Profile', icon: 'profile' },
  ],
}

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
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  min-width: 4.3rem;
  padding: 0.2rem 0.15rem;
  color: var(--tg-hint, #8592a3);
  transition: color 0.2s ease;
}

.nav-link__icon {
  width: 2.45rem;
  height: 2.45rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  transition:
    background 0.22s ease,
    color 0.22s ease,
    box-shadow 0.22s ease;
}

.nav-link__icon svg {
  width: 1.32rem;
  height: 1.32rem;
}

.nav-link__icon path {
  stroke: currentColor;
  stroke-width: 1.95;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.nav-link__label {
  font-size: 0.73rem;
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0.01em;
  white-space: nowrap;
}

.nav-link:hover .nav-link__icon {
  color: var(--tg-link, #229ed9);
  background: rgba(34, 158, 217, 0.14);
}

.nav-link.router-link-active {
  color: var(--tg-text, #18222d);
}

.nav-link.router-link-active .nav-link__icon {
  color: var(--tg-button-text, #ffffff);
  background: linear-gradient(155deg, var(--tg-button, #229ed9), #1b8ac6);
  box-shadow: 0 10px 24px rgba(34, 158, 217, 0.38);
}

.nav-link.router-link-active .nav-link__label {
  color: var(--tg-text, #18222d);
}
</style>
