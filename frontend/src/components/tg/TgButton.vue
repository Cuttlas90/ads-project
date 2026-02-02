<template>
  <button
    class="tg-button"
    :class="[`tg-button--${variant}`, `tg-button--${size}`, { 'tg-button--full': fullWidth }]"
    :disabled="disabled || loading"
    type="button"
  >
    <span v-if="loading" class="tg-button__spinner" aria-hidden="true"></span>
    <span class="tg-button__label"><slot /></span>
  </button>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  disabled?: boolean
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  fullWidth: false,
  disabled: false,
  loading: false,
})
</script>

<style scoped>
.tg-button {
  border: none;
  cursor: pointer;
  border-radius: var(--app-radius-md);
  padding: 0.75rem 1.25rem;
  font-weight: 600;
  font-size: 0.95rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition:
    transform 0.15s ease,
    box-shadow 0.2s ease,
    opacity 0.2s ease;
}

.tg-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.tg-button--full {
  width: 100%;
  justify-content: center;
}

.tg-button--primary {
  background: linear-gradient(135deg, var(--tg-button), #065f5b);
  color: var(--tg-button-text);
  box-shadow: var(--app-shadow);
}

.tg-button--secondary {
  background: var(--app-surface);
  color: var(--app-ink);
  border: 1px solid var(--app-border);
}

.tg-button--ghost {
  background: transparent;
  color: var(--app-ink);
  border: 1px dashed rgba(25, 25, 25, 0.25);
}

.tg-button--sm {
  padding: 0.45rem 0.85rem;
  font-size: 0.85rem;
}

.tg-button--lg {
  padding: 0.95rem 1.5rem;
  font-size: 1.05rem;
}

.tg-button__spinner {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: rgba(255, 255, 255, 0.9);
  animation: spin 0.8s linear infinite;
}

.tg-button--secondary .tg-button__spinner,
.tg-button--ghost .tg-button__spinner {
  border-color: rgba(25, 25, 25, 0.25);
  border-top-color: rgba(25, 25, 25, 0.85);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
