import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "path";

export default defineConfig(({ command }) => ({
  plugins: [react(), tailwindcss()],
  publicDir: "public-local",
  define: command === "build"
    ? { "import.meta.env.VITE_API_URL": JSON.stringify("") }
    : {},
  build: {
    outDir: "../validex/static",
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
    globals: true,
  },
}));
