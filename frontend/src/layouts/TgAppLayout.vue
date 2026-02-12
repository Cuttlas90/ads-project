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
  padding: 1.25rem 1.5rem 5rem;
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
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.75rem 1.5rem calc(0.75rem + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.94);
  border-top: 1px solid rgba(20, 20, 20, 0.08);
  display: flex;
  justify-content: space-around;
  gap: 0.75rem;
}

@media (min-width: 720px) {
  .app-shell {
    max-width: 960px;
    margin: 0 auto;
  }
  .app-bottomnav {
    left: 50%;
    transform: translateX(-50%);
    max-width: 960px;
    border-radius: 18px 18px 0 0;
  }
  .app-top-notifications {
    max-width: 960px;
    margin: 0.6rem auto 0;
    width: 100%;
  }
}
</style>
