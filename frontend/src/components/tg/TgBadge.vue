<template>
  <span class="tg-badge" :class="`tg-badge--${tone}`"><slot /></span>
</template>

<script setup lang="ts">
interface Props {
  tone?: 'neutral' | 'success' | 'warning' | 'danger'
}

withDefaults(defineProps<Props>(), {
  tone: 'neutral',
})
</script>

<style scoped>
.tg-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.tg-badge--neutral {
  background: rgba(25, 25, 25, 0.08);
  color: var(--app-ink);
}

.tg-badge--success {
  background: rgba(42, 157, 143, 0.18);
  color: var(--app-success);
}

.tg-badge--warning {
  background: rgba(244, 162, 97, 0.22);
  color: #a3561a;
}

.tg-badge--danger {
  background: rgba(214, 69, 80, 0.18);
  color: var(--app-danger);
}
</style>
