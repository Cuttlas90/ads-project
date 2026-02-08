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

    <TgCard title="TON wallet" subtitle="Connect wallet ownership proof for payouts and refunds.">
      <div class="profile__status">
        <span class="profile__label">Wallet status</span>
        <TgBadge :tone="hasWallet ? 'success' : 'warning'">
          {{ hasWallet ? 'Connected' : 'Not connected' }}
        </TgBadge>
      </div>

      <p class="profile__copy">
        Wallet setup is optional for role selection, but funding requires a connected wallet.
      </p>

      <code v-if="walletDisplayAddress" class="profile__wallet">{{ walletDisplayAddress }}</code>

      <div class="profile__actions">
        <TgButton full-width :loading="walletLoading" @click="startWalletProof">
          {{ hasWallet ? 'Update TON Wallet' : 'Connect TON Wallet' }}
        </TgButton>
        <TgButton v-if="nextPath && hasWallet" full-width variant="secondary" @click="goToNextPath">
          Return to Funding
        </TgButton>
      </div>

      <p v-if="nextPath && !hasWallet" class="profile__next-copy">
        Connect wallet, then you will be sent back to funding.
      </p>

      <TgStatePanel v-if="walletError" title="Wallet connection failed" :description="walletError">
        <template #icon>!</template>
      </TgStatePanel>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { TonConnectUI } from '@tonconnect/ui'
import type { TonProofItemReplySuccess, Wallet } from '@tonconnect/sdk'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { TgBadge, TgButton, TgCard, TgStatePanel } from '../components/tg'
import { usersService } from '../services/users'
import { useAuthStore } from '../stores/auth'
import type { RolePreference } from '../types/api'
import { toWalletFriendlyAddress } from '../utils/tonAddress'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const selectingRole = ref<RolePreference | null>(null)
const walletLoading = ref(false)
const walletError = ref('')
const pendingChallenge = ref<string | null>(null)
const tonUi = ref<TonConnectUI | null>(null)

let unsubscribeWalletStatus: (() => void) | null = null

const currentRole = computed(() => authStore.user?.preferred_role ?? null)
const hasWallet = computed(() => authStore.user?.has_wallet ?? false)
const walletAddress = computed(() => authStore.user?.ton_wallet_address ?? null)
const walletDisplayAddress = computed(() => {
  if (!walletAddress.value) {
    return null
  }
  return toWalletFriendlyAddress(walletAddress.value)
})

const nextPath = computed(() => {
  const next = route.query.next
  if (typeof next !== 'string') {
    return null
  }
  if (!next.startsWith('/')) {
    return null
  }
  return next
})

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

const ensureTonUi = (): TonConnectUI | null => {
  if (tonUi.value) {
    return tonUi.value
  }

  const manifestUrl = import.meta.env.VITE_TONCONNECT_MANIFEST_URL
  if (!manifestUrl) {
    walletError.value = 'Missing TONConnect manifest URL'
    return null
  }

  tonUi.value = new TonConnectUI({
    manifestUrl,
  })

  unsubscribeWalletStatus = tonUi.value.onStatusChange(
    (wallet) => {
      void handleWalletStatus(wallet)
    },
    (error) => {
      if (!pendingChallenge.value) {
        return
      }
      walletError.value = error.message
      pendingChallenge.value = null
      tonUi.value?.setConnectRequestParameters(null)
    },
  )

  return tonUi.value
}

const extractTonProof = (wallet: Wallet | null): TonProofItemReplySuccess['proof'] | null => {
  const tonProof = wallet?.connectItems?.tonProof
  if (!tonProof || !('proof' in tonProof)) {
    return null
  }
  return tonProof.proof
}

const handleWalletStatus = async (wallet: Wallet | null) => {
  const challenge = pendingChallenge.value
  if (!challenge) {
    return
  }

  const proof = extractTonProof(wallet)
  if (!wallet || !proof) {
    return
  }

  walletLoading.value = true
  walletError.value = ''
  try {
    await usersService.verifyWalletProof({
      account: {
        address: wallet.account.address,
        chain: wallet.account.chain,
        walletStateInit: wallet.account.walletStateInit,
        publicKey: wallet.account.publicKey ?? null,
      },
      proof: {
        timestamp: proof.timestamp,
        domain: {
          lengthBytes: proof.domain.lengthBytes,
          value: proof.domain.value,
        },
        signature: proof.signature,
        payload: challenge,
      },
    })

    pendingChallenge.value = null
    tonUi.value?.setConnectRequestParameters(null)
    await authStore.fetchMe()

    if (nextPath.value && authStore.user?.has_wallet) {
      await router.push(nextPath.value)
    }
  } catch (error) {
    walletError.value = error instanceof Error ? error.message : 'Wallet verification failed'
    pendingChallenge.value = null
    tonUi.value?.setConnectRequestParameters(null)
  } finally {
    walletLoading.value = false
  }
}

const startWalletProof = async () => {
  walletLoading.value = true
  walletError.value = ''

  try {
    const ui = ensureTonUi()
    if (!ui) {
      return
    }

    const challenge = await usersService.issueWalletChallenge()
    pendingChallenge.value = challenge.challenge

    ui.setConnectRequestParameters({
      state: 'ready',
      value: {
        tonProof: challenge.challenge,
      },
    })

    await ui.openModal()
  } catch (error) {
    walletError.value = error instanceof Error ? error.message : 'Failed to connect wallet'
    pendingChallenge.value = null
    tonUi.value?.setConnectRequestParameters(null)
  } finally {
    walletLoading.value = false
  }
}

const goToNextPath = async () => {
  if (!nextPath.value) {
    return
  }
  await router.push(nextPath.value)
}

onMounted(() => {
  ensureTonUi()
})

onBeforeUnmount(() => {
  unsubscribeWalletStatus?.()
  unsubscribeWalletStatus = null
  tonUi.value?.setConnectRequestParameters(null)
})
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

.profile__wallet {
  margin-top: 0.75rem;
  display: block;
  padding: 0.6rem;
  border-radius: var(--app-radius-md);
  background: var(--app-bg-soft);
  color: var(--app-ink);
  overflow-wrap: anywhere;
}

.profile__actions {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}

.profile__next-copy {
  margin-top: 0.75rem;
  color: var(--app-ink-muted);
}
</style>
