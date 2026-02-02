<template>
  <section class="tg-list">
    <header v-if="title" class="tg-list__header">
      <h4>{{ title }}</h4>
      <p v-if="subtitle">{{ subtitle }}</p>
    </header>
    <div class="tg-list__body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  subtitle?: string
}

defineProps<Props>()
</script>

<style scoped>
.tg-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tg-list__header h4 {
  margin: 0;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--app-ink-muted);
}

.tg-list__header p {
  margin: 0.25rem 0 0 0;
  font-size: 0.85rem;
  color: var(--app-ink-muted);
}

.tg-list__body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
