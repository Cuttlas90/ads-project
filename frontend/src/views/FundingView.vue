<template>
  <section class="funding">
    <TgCard title="Fund escrow" subtitle="Approve in TONConnect, then wait for confirmations.">
      <TgStatePanel v-if="error" title="Funding issue" :description="error">
        <template #icon>!</template>
      </TgStatePanel>

      <div class="funding__body">
        <TgButton full-width :loading="loading" @click="initFunding"
          >Generate TONConnect request</TgButton
        >
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
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { TonConnectUI } from '@tonconnect/ui'

import { TgButton, TgCard, TgStatePanel } from '../components/tg'
import { dealsService } from '../services/deals'

const route = useRoute()
const dealId = Number(route.params.id)

const loading = ref(false)
const error = ref('')
const escrow = ref<Record<string, unknown> | null>(null)
const tonUi = ref<TonConnectUI | null>(null)
const poller = ref<number | null>(null)

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

const initFunding = async () => {
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

onMounted(() => {
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
</style>
