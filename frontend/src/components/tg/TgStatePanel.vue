<template>
  <div class="tg-state" :class="`tg-state--${tone}`">
    <div class="tg-state__icon">
      <slot name="icon">◎</slot>
    </div>
    <div class="tg-state__content">
      <h3>{{ title }}</h3>
      <p v-if="description">{{ description }}</p>
      <div v-if="$slots.action" class="tg-state__action">
        <slot name="action" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  description?: string
  tone?: 'neutral' | 'success' | 'warning' | 'danger'
}

withDefaults(defineProps<Props>(), {
  tone: 'neutral',
})
</script>

<style scoped>
.tg-state {
  --tg-state-bg: var(--app-notif-neutral-bg);
  --tg-state-fg: var(--app-notif-neutral-fg);
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: var(--app-radius-lg);
  background: var(--tg-state-bg);
  color: var(--tg-state-fg);
  border: 1px solid var(--app-notif-border);
}

.tg-state__icon {
  font-size: 1.6rem;
}

.tg-state__content h3 {
  margin: 0;
}

.tg-state__content p {
  margin: 0.35rem 0 0 0;
  color: var(--tg-state-fg);
  opacity: 0.82;
}

.tg-state__action {
  margin-top: 0.85rem;
}

.tg-state--success {
  --tg-state-bg: var(--app-notif-success-bg);
  --tg-state-fg: var(--app-notif-success-fg);
}

.tg-state--warning {
  --tg-state-bg: var(--app-notif-warning-bg);
  --tg-state-fg: var(--app-notif-warning-fg);
}

.tg-state--danger {
  --tg-state-bg: var(--app-notif-danger-bg);
  --tg-state-fg: var(--app-notif-danger-fg);
}
</style>
