import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { initTelegramThemeBridge } from './services/telegramTheme'
import './style.css'

const stopThemeBridge = initTelegramThemeBridge()

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    stopThemeBridge()
  })
}
