import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@/components": path.resolve(__dirname, "./src/components"),
      "@/pages": path.resolve(__dirname, "./src/pages"),
      "@/assets": path.resolve(__dirname, "./src/assets"),
      "@/styles": path.resolve(__dirname, "./src/styles"),
      "@/api": path.resolve(__dirname, "./src/api"),
      "@/hooks": path.resolve(__dirname, "./src/hooks"),
      "@/lib": path.resolve(__dirname, "./src/lib"),
    },
  },
  // DEV-сервер (npm run dev)
  server: {
    host: true, // слушать на всех интерфейсах (0.0.0.0)
    port: 5173, // можно любой
    allowedHosts: [
      "techno-shark.ru",
      "localhost",
      "127.0.0.1",
    ],
  },

  // PREVIEW (npm run preview)
  preview: {
    host: true,
    port: 4173,
    allowedHosts: [
      "techno-shark.ru",
      "localhost",
      "127.0.0.1",
    ],
  },
});
