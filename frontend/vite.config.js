import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In Docker, the backend is reachable at the service name "backend"; when
// running the frontend directly on the host with `npm run dev`, it's just
// localhost. VITE_API_PROXY_TARGET lets docker-compose override this.
const proxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
})
