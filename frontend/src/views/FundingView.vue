<template>
  <section class="funding">
    <TgCard title="Fund escrow" subtitle="Approve in TONConnect, then wait for confirmations.">
      <TgStatePanel v-if="fundingError" tone="danger" title="Funding issue" :description="fundingError">
        <template #icon>!</template>
      </TgStatePanel>

      <div class="funding__body">
        <TgButton
          full-width
          :loading="loading"
          :disabled="walletMissing"
          @click="initFunding"
        >
          {{ walletMissing ? 'Connect wallet in Profile to continue' : 'Generate TONConnect request' }}
        </TgButton>
        <div id="tonconnect-button" class="funding__ton" />

        <TgCard v-if="escrow" title="Escrow status" :padded="false">
          <div class="funding__status">
            <p><strong>State:</strong> {{ escrow.state }}</p>
            <p>
              <strong>Received:</strong> {{ escrow.received_amount_ton ?? '0' }} /
              {{ escrow.expected_amount_ton ?? '--' }} TON
            </p>
            <p><strong>Confirmations:</strong> {{ escrow.deposit_confirmations }}</p>
          </div>
        </TgCard>
      </div>
    </TgCard>

    <TgModal :open="walletGateOpen" title="Wallet required" :close-on-backdrop="false" @close="closeWalletGate">
      <p class="funding__modal-copy">
        Funding is blocked until your advertiser wallet is connected. Refund flows depend on this wallet.
      </p>
      <template #footer>
        <div class="funding__modal-actions">
          <TgButton full-width @click="goToProfile">Go to Profile</TgButton>
        </div>
      </template>
    </TgModal>
  </section>
</template>

<script setup lang="ts">
import { TonConnectUI } from '@tonconnect/ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { TgButton, TgCard, TgModal, TgStatePanel } from '../components/tg'
import { dealsService } from '../services/deals'
import { useAuthStore } from '../stores/auth'
import { useNotificationsStore } from '../stores/notifications'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const dealId = Number(route.params.id)

const loading = ref(false)
const fundingError = ref('')
const escrow = ref<Record<string, unknown> | null>(null)
const tonUi = ref<TonConnectUI | null>(null)
const poller = ref<number | null>(null)
const walletGateOpen = ref(false)

const walletMissing = computed(() => !(authStore.user?.has_wallet ?? false))

const initTonConnect = () => {
  if (tonUi.value) return
  const manifestUrl = import.meta.env.VITE_TONCONNECT_MANIFEST_URL
  if (!manifestUrl) {
    fundingError.value = 'Missing TONConnect manifest URL'
    return
  }
  tonUi.value = new TonConnectUI({
    manifestUrl,
    buttonRootId: 'tonconnect-button',
    actionsConfiguration: {
      modals: [],
      notifications: [],
    },
  })
}

const openWalletGate = () => {
  walletGateOpen.value = true
}

const closeWalletGate = () => {
  walletGateOpen.value = false
}

const goToProfile = async () => {
  await router.push({
    path: '/profile',
    query: {
      next: route.fullPath,
    },
  })
}

const initFunding = async () => {
  if (walletMissing.value) {
    openWalletGate()
    return
  }

  loading.value = true
  fundingError.value = ''
  try {
    initTonConnect()
    if (!tonUi.value) return
    await dealsService.escrowInit(dealId)
    const { payload } = await dealsService.tonconnectTx(dealId)
    notificationsStore.pushToast({
      tone: 'neutral',
      source: 'funding',
      message: 'Open your wallet to approve the transaction.',
    })
    await tonUi.value.sendTransaction(payload as Record<string, unknown>, {
      modals: [],
      notifications: [],
    })
    notificationsStore.pushToast({
      tone: 'success',
      source: 'funding',
      message: 'Transaction submitted. Waiting for confirmations.',
    })
    startPolling()
    void pollStatus()
  } catch (err) {
    fundingError.value = err instanceof Error ? err.message : 'Failed to initialize funding'
    notificationsStore.pushToast({
      tone: 'danger',
      source: 'funding',
      dedupeKey: `funding-init-${dealId}-${fundingError.value}`,
      message: fundingError.value,
    })
  } finally {
    loading.value = false
  }
}

const pollStatus = async () => {
  try {
    const status = (await dealsService.escrowStatus(dealId)) as Record<string, unknown>
    escrow.value = status
    fundingError.value = ''

    const state = typeof status.state === 'string' ? status.state : ''
    if (state === 'FUNDED') {
      notificationsStore.pushToast({
        tone: 'success',
        source: 'funding',
        dedupeKey: `funding-state-funded-${dealId}`,
        message: 'Escrow funded successfully.',
      })
      stopPolling()
      return
    }
    if (state === 'FAILED') {
      notificationsStore.pushToast({
        tone: 'danger',
        source: 'funding',
        dedupeKey: `funding-state-failed-${dealId}`,
        message: 'Escrow funding failed. Please review and retry.',
      })
      stopPolling()
    }
  } catch (err) {
    fundingError.value = err instanceof Error ? err.message : 'Failed to fetch escrow status'
    notificationsStore.pushToast({
      tone: 'warning',
      source: 'funding',
      dedupeKey: `funding-poll-${dealId}-${fundingError.value}`,
      message: fundingError.value,
    })
  }
}

const stopPolling = () => {
  if (poller.value) {
    window.clearInterval(poller.value)
    poller.value = null
  }
}

const startPolling = () => {
  if (poller.value) return
  poller.value = window.setInterval(() => {
    void pollStatus()
  }, 4000)
}

watch(walletMissing, (missing) => {
  if (missing) {
    stopPolling()
    openWalletGate()
    return
  }

  closeWalletGate()
  initTonConnect()
  void pollStatus()
})

onMounted(() => {
  if (walletMissing.value) {
    openWalletGate()
    return
  }

  initTonConnect()
  void pollStatus()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
.funding__body {
  display: grid;
  gap: 1rem;
}

.funding__ton {
  display: flex;
  justify-content: center;
}

.funding__status {
  padding: 1rem;
  color: var(--app-ink-muted);
}

.funding__modal-copy {
  margin: 0;
  color: var(--app-ink-muted);
}

.funding__modal-actions {
  display: flex;
  width: 100%;
}
</style>
