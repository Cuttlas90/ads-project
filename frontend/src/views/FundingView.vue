<template>
  <section class="funding">
    <TgCard title="Fund escrow" subtitle="Approve in TONConnect, then wait for confirmations.">
      <TgStatePanel v-if="error" title="Funding issue" :description="error">
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

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const dealId = Number(route.params.id)

const loading = ref(false)
const error = ref('')
const escrow = ref<Record<string, unknown> | null>(null)
const tonUi = ref<TonConnectUI | null>(null)
const poller = ref<number | null>(null)
const walletGateOpen = ref(false)

const walletMissing = computed(() => !(authStore.user?.has_wallet ?? false))

const initTonConnect = () => {
  if (tonUi.value) return
  const manifestUrl = import.meta.env.VITE_TONCONNECT_MANIFEST_URL
  if (!manifestUrl) {
    error.value = 'Missing TONConnect manifest URL'
    return
  }
  tonUi.value = new TonConnectUI({
    manifestUrl,
    buttonRootId: 'tonconnect-button',
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
  error.value = ''
  try {
    initTonConnect()
    if (!tonUi.value) return
    await dealsService.escrowInit(dealId)
    const { payload } = await dealsService.tonconnectTx(dealId)
    await tonUi.value.sendTransaction(payload as Record<string, unknown>)
    startPolling()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to initialize funding'
  } finally {
    loading.value = false
  }
}

const pollStatus = async () => {
  try {
    escrow.value = await dealsService.escrowStatus(dealId)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch escrow status'
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
  if (poller.value) {
    window.clearInterval(poller.value)
  }
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
