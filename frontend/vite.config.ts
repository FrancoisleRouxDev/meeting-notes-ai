import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // The browser talks only to the Vite server, which forwards /api to FastAPI.
      // The path is kept as it is, because the backend mounts its routes under /api.
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
