import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Blantyre Synod Schools',
        short_name: 'Blantyre Schools',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        theme_color: '#2b6cb0',
        icons: []
      }
    })
  ],
  server: {
    port: 5173
  }
})



