import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1024,
  },
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
});
