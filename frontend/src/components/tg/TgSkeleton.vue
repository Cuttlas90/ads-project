<template>
  <div class="tg-skeleton" :style="style"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  width?: string
  height?: string
  radius?: string
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '14px',
  radius: '999px',
})

const style = computed(() => ({
  width: props.width,
  height: props.height,
  borderRadius: props.radius,
}))
</script>

<style scoped>
.tg-skeleton {
  background: linear-gradient(
    90deg,
    rgba(20, 20, 20, 0.08),
    rgba(20, 20, 20, 0.16),
    rgba(20, 20, 20, 0.08)
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
