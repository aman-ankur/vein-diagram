import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';

// Create HTML history fallback
const createFallback = () => {
  return {
    name: 'html-history-fallback',
    writeBundle() {
      // Create _redirects file for Netlify/Vercel
      fs.writeFileSync(
        path.resolve(__dirname, 'dist/_redirects'),
        '/*    /index.html   200'
      );
    }
  };
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), createFallback()],
  server: {
    port: 3001,
    strictPort: true,
    open: '/', // Open the main React app
    historyApiFallback: true, // SPA route handling in dev mode
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
}); 