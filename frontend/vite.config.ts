import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Frontend never talks to the Sepolia RPC directly (CLAUDE.md rule). All
// /api/* requests are proxied to the backend on :8000 so the browser sees
// a same-origin cookie and the RPC URL stays server-side.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: false,
      },
    },
  },
});
