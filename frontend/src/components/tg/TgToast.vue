<template>
  <transition name="toast">
    <div v-if="visible" class="tg-toast" :class="`tg-toast--${tone}`">
      <span>{{ message }}</span>
      <button v-if="dismissible" class="tg-toast__close" type="button" @click="emit('dismiss')">
        ×
      </button>
    </div>
  </transition>
</template>

<script setup lang="ts">
interface Props {
  message: string
  tone?: 'neutral' | 'success' | 'warning' | 'danger'
  visible?: boolean
  dismissible?: boolean
}

withDefaults(defineProps<Props>(), {
  tone: 'neutral',
  visible: true,
  dismissible: true,
})

const emit = defineEmits<{ dismiss: [] }>()
</script>

<style scoped>
.tg-toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: var(--app-radius-md);
  font-size: 0.9rem;
  box-shadow: var(--app-shadow);
  border: 1px solid var(--app-notif-border);
}

.tg-toast--neutral {
  background: var(--app-notif-neutral-bg);
  color: var(--app-notif-neutral-fg);
}

.tg-toast--success {
  background: var(--app-notif-success-bg);
  color: var(--app-notif-success-fg);
}

.tg-toast--warning {
  background: var(--app-notif-warning-bg);
  color: var(--app-notif-warning-fg);
}

.tg-toast--danger {
  background: var(--app-notif-danger-bg);
  color: var(--app-notif-danger-fg);
}

.tg-toast__close {
  border: none;
  background: transparent;
  font-size: 1.1rem;
  cursor: pointer;
  color: currentColor;
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
