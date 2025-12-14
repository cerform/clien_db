import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite config for dev-time proxying of /api to local backend (useful in CI and dev)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
