import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  css: ['./app/assets/css/main.css'],
  base: '/',
  optimizeDeps: {
    include: ['quagga'],
  },
  plugins: [
    vue(),
    vueJsx(),
    tailwindcss(),
    vueDevTools(),
    VitePWA({ registerType: 'autoUpdate', devOptions: { enabled: true }, manifest: {} }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
