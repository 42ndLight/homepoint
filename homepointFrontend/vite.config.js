import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'


// https://vite.dev/config/
export default defineConfig({
  base: '/',
  optimizeDeps: {
    include: ['quagga'],
  },
  plugins: [
    vue(),
    vueJsx(),
    tailwindcss(),
    process.env.NODE_ENV !== 'production' && vueDevTools(),
    VitePWA({ registerType: 'autoUpdate', devOptions: { enabled: true }, manifest: {} }),
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // Allows access from other devices/hosts
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    // Allows Docker network proxies or service names to request files
    allowedHosts: true,
    // Permits your browser to safely request files across your docker-compose local containers
    cors: true
  },
  preview: {
    host: true,
    port: 4173
  }
})
