import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  // ассеты отдаёт WordPress из темы
  base: '/wp-content/themes/davidv/assets/build/',
  build: {
    manifest: true,
    outDir: resolve(__dirname, 'assets/build'),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'assets/src/main.js'),
    },
  },
});
