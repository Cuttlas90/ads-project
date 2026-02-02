<template>
  <section class="tg-card" :class="{ 'tg-card--padded': padded }">
    <header v-if="title" class="tg-card__header">
      <h3>{{ title }}</h3>
      <p v-if="subtitle">{{ subtitle }}</p>
    </header>
    <div class="tg-card__body">
      <slot />
    </div>
    <footer v-if="$slots.footer" class="tg-card__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  subtitle?: string
  padded?: boolean
}

withDefaults(defineProps<Props>(), {
  padded: true,
})
</script>

<style scoped>
.tg-card {
  background: var(--app-surface);
  border-radius: var(--app-radius-lg);
  border: 1px solid var(--app-border);
  box-shadow: var(--app-shadow);
}

.tg-card--padded {
  padding: 1.25rem;
}

.tg-card__header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.05rem;
}

.tg-card__header p {
  margin: 0;
  color: var(--app-ink-muted);
  font-size: 0.9rem;
}

.tg-card__body {
  margin-top: 0.75rem;
}

.tg-card__footer {
  margin-top: 1rem;
}
</style>
