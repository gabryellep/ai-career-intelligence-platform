/**
 * vite.config.js — Configuração do Vite para o AI Resume Analyzer.
 *
 * - Plugin React: habilita JSX e Fast Refresh em desenvolvimento.
 * - Proxy: redireciona chamadas /health, /analyze e /api para o backend
 *   FastAPI em http://localhost:8000, evitando problemas de CORS em
 *   desenvolvimento. /api cobre os endpoints de histórico e analytics
 *   (SPEC 0005/0006), consumidos pela área de Histórico e Dashboard
 *   (SPEC 0007).
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    proxy: {
      // Redireciona /analyze, /health e /api para o backend FastAPI
      '/analyze': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
