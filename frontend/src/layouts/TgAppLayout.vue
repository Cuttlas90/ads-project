<template>
  <div class="app-shell">
    <header class="app-topbar">
      <div class="app-topbar__title">
        <slot name="title">Telegram Ads</slot>
      </div>
      <div class="app-topbar__actions">
        <slot name="actions" />
      </div>
    </header>

    <div v-if="$slots['top-notifications']" class="app-top-notifications">
      <slot name="top-notifications" />
    </div>

    <main class="app-main">
      <slot />
    </main>

    <nav v-if="$slots.nav" class="app-bottomnav">
      <slot name="nav" />
    </nav>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom)
    env(safe-area-inset-left);
}

.app-topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem 1rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(244, 241, 234, 0.9));
  border-bottom: 1px solid rgba(20, 20, 20, 0.08);
  backdrop-filter: blur(12px);
}

.app-topbar__title {
  font-weight: 700;
  font-size: 1.15rem;
}

.app-main {
  flex: 1;
  padding: 1.25rem 1.5rem 6.35rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.app-top-notifications {
  margin-top: 0.6rem;
  padding: 0 1.5rem;
  z-index: 11;
}

.app-bottomnav {
  position: fixed;
  bottom: 0.65rem;
  left: 0.85rem;
  right: 0.85rem;
  padding: 0.5rem 0.55rem calc(0.5rem + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(245, 249, 253, 0.95));
  border: 1px solid rgba(27, 77, 113, 0.15);
  border-radius: 22px;
  box-shadow:
    0 15px 36px rgba(22, 58, 90, 0.2),
    0 2px 0 rgba(255, 255, 255, 0.55) inset;
  backdrop-filter: blur(16px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.25rem;
  z-index: 30;
}

@media (min-width: 720px) {
  .app-shell {
    max-width: 960px;
    margin: 0 auto;
  }
  .app-bottomnav {
    left: 50%;
    right: auto;
    transform: translateX(-50%);
    max-width: 960px;
    width: calc(100% - 2rem);
  }
  .app-top-notifications {
    max-width: 960px;
    margin: 0.6rem auto 0;
    width: 100%;
  }
}
</style>
