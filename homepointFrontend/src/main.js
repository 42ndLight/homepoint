import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
/*
import 'primevue/resources/themes/saga-blue/theme.css' // Or your preferred theme
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css
*/
import Aura from '@primeuix/themes/aura'

import App from './App.vue'
import router from './router'

import 'primeicons/primeicons.css'
import './assests/css/style.css'


const app = createApp(App)

app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: '.home-point-dark',
            cssLayer: {
                name: 'primevue',
                order: 'theme, base, primevue'
        },
    },
  },
  ripple: true,
})

app.use(ToastService)
app.use(createPinia())
app.use(router)

app.mount('#app')
