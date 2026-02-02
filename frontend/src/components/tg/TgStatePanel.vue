<template>
  <div class="tg-state">
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
}

defineProps<Props>()
</script>

<style scoped>
.tg-state {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: var(--app-radius-lg);
  background: var(--app-surface-muted);
  border: 1px dashed rgba(25, 25, 25, 0.15);
}

.tg-state__icon {
  font-size: 1.6rem;
}

.tg-state__content h3 {
  margin: 0;
}

.tg-state__content p {
  margin: 0.35rem 0 0 0;
  color: var(--app-ink-muted);
}

.tg-state__action {
  margin-top: 0.85rem;
}
</style>
