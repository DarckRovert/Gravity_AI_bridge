import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    // Sacar el build de frontend/dist/ (sincronizado por Google Drive)
    // a web/ en la raíz del proyecto — que el bridge_server ya sirve como
    // primera opción en _serve_dashboard() y NO es monitoreado por Drive.
    outDir: '../web',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react';
          }
          if (id.includes('node_modules/lucide-react')) {
            return 'lucide';
          }
        }
      }
    }
  }
})
