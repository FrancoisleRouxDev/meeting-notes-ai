import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // The browser talks only to the Vite server, which forwards /api to FastAPI.
      // That keeps the session cookie on one origin. Calling 127.0.0.1 directly from
      // localhost would be a different site, so the browser would block the cookie.
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});