<template>
  <section class="resolver">
    <TgCard title="Loading" subtitle="Resolving your role preferences.">
      <TgSkeleton height="80px" />
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { TgCard, TgSkeleton } from '../components/tg'
</script>

<style scoped>
.resolver {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
