import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Serve the API from the app's own origin so the login cookies are
    // first-party (localhost and 127.0.0.1 are different sites).
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
})
