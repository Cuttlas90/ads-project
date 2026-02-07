<template>
  <section class="profile">
    <TgCard title="Profile" subtitle="Manage your role for this account.">
      <div class="profile__status">
        <span class="profile__label">Current role</span>
        <TgBadge :tone="currentRole ? 'success' : 'warning'">{{ currentRoleLabel }}</TgBadge>
      </div>

      <p class="profile__copy">
        Choose your role to continue. You can change this role anytime from Profile.
      </p>

      <div class="profile__actions">
        <TgButton
          full-width
          :variant="currentRole === 'owner' ? 'primary' : 'secondary'"
          :loading="selectingRole === 'owner'"
          :disabled="selectingRole !== null"
          @click="selectRole('owner')"
        >
          I'm a Channel Owner
        </TgButton>
        <TgButton
          full-width
          :variant="currentRole === 'advertiser' ? 'primary' : 'secondary'"
          :loading="selectingRole === 'advertiser'"
          :disabled="selectingRole !== null"
          @click="selectRole('advertiser')"
        >
          I'm an Advertiser
        </TgButton>
      </div>

      <TgStatePanel
        v-if="authStore.error"
        title="Unable to save your role"
        :description="authStore.error"
      >
        <template #icon>!</template>
      </TgStatePanel>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { TgBadge, TgButton, TgCard, TgStatePanel } from '../components/tg'
import { useAuthStore } from '../stores/auth'
import type { RolePreference } from '../types/api'

const authStore = useAuthStore()
const selectingRole = ref<RolePreference | null>(null)

const currentRole = computed(() => authStore.user?.preferred_role ?? null)
const currentRoleLabel = computed(() => {
  if (currentRole.value === 'owner') {
    return 'Channel Owner'
  }
  if (currentRole.value === 'advertiser') {
    return 'Advertiser'
  }
  return 'Not selected'
})

const selectRole = async (role: RolePreference) => {
  if (selectingRole.value !== null) {
    return
  }
  selectingRole.value = role
  try {
    await authStore.setPreferredRole(role)
  } finally {
    selectingRole.value = null
  }
}
</script>

<style scoped>
.profile {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.profile__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.profile__label {
  font-weight: 600;
  color: var(--app-ink-muted);
}

.profile__copy {
  margin: 0.9rem 0 0;
  color: var(--app-ink-muted);
}

.profile__actions {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}
</style>
