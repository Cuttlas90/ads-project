<template>
  <div v-if="toasts.length" class="tg-toast-stack" role="status" aria-live="polite">
    <TgToast
      v-for="toast in toasts"
      :key="toast.id"
      :message="toast.message"
      :tone="toast.tone"
      :dismissible="toast.dismissible"
      @dismiss="notificationsStore.dismissToast(toast.id)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useNotificationsStore } from '../../stores/notifications'
import TgToast from './TgToast.vue'

const notificationsStore = useNotificationsStore()
const toasts = computed(() => notificationsStore.toasts)
</script>

<style scoped>
.tg-toast-stack {
  width: min(92vw, 560px);
  margin: 0 auto;
  display: grid;
  gap: 0.55rem;
  pointer-events: none;
}

.tg-toast-stack :deep(.tg-toast) {
  pointer-events: auto;
}
</style>
