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
}

.tg-toast--neutral {
  background: var(--app-surface);
  color: var(--app-ink);
}

.tg-toast--success {
  background: rgba(42, 157, 143, 0.16);
  color: var(--app-success);
}

.tg-toast--warning {
  background: rgba(244, 162, 97, 0.2);
  color: #a3561a;
}

.tg-toast--danger {
  background: rgba(214, 69, 80, 0.18);
  color: var(--app-danger);
}

.tg-toast__close {
  border: none;
  background: transparent;
  font-size: 1.1rem;
  cursor: pointer;
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
