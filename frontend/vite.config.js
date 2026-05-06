/**
 * vite.config.js — Configuração do Vite para o AI Resume Analyzer.
 *
 * - Plugin React: habilita JSX e Fast Refresh em desenvolvimento.
 * - Proxy: redireciona chamadas /health e /analyze para o backend FastAPI
 *   em http://localhost:8000, evitando problemas de CORS em desenvolvimento.
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    proxy: {
      // Redireciona /analyze e /health para o backend FastAPI
      '/analyze': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
