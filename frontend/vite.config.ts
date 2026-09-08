import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  // The lazy 3D route contains Three.js and React Three Fiber. Its gzip size is
  // roughly 253 KB; this limit keeps warnings focused on unexpected growth.
  build: { chunkSizeWarningLimit: 1000 },
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
});
