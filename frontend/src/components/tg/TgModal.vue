<template>
  <teleport to="body">
    <div v-if="open" class="tg-modal">
      <div class="tg-modal__backdrop" @click="onBackdrop"></div>
      <div class="tg-modal__panel" :style="{ '--tg-modal-max-width': props.maxWidth }">
        <header class="tg-modal__header">
          <h3>{{ title }}</h3>
          <button class="tg-modal__close" type="button" @click="emit('close')">×</button>
        </header>
        <div class="tg-modal__body">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="tg-modal__footer">
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
interface Props {
  open: boolean
  title: string
  closeOnBackdrop?: boolean
  maxWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  closeOnBackdrop: true,
  maxWidth: '420px',
})

const emit = defineEmits<{ close: [] }>()

const onBackdrop = () => {
  if (props.closeOnBackdrop) {
    emit('close')
  }
}
</script>

<style scoped>
.tg-modal {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1rem;
  z-index: 50;
}

.tg-modal__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(10, 10, 10, 0.45);
  backdrop-filter: blur(6px);
}

.tg-modal__panel {
  position: relative;
  width: min(92vw, var(--tg-modal-max-width, 420px));
  max-height: calc(100vh - 2rem);
  background: var(--app-surface);
  border-radius: var(--app-radius-lg);
  padding: 1.25rem;
  box-shadow: var(--app-shadow);
  z-index: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: rise 0.2s ease-out;
}

.tg-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  flex-shrink: 0;
}

.tg-modal__header h3 {
  margin: 0;
}

.tg-modal__close {
  border: none;
  background: transparent;
  font-size: 1.4rem;
  cursor: pointer;
}

.tg-modal__body {
  min-height: 0;
  overflow-y: auto;
}

.tg-modal__footer {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--app-border);
  flex-shrink: 0;
}

@keyframes rise {
  from {
    transform: translateY(10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
