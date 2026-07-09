import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // host: true -> escucha en todas las interfaces (IPv4 y IPv6), para
    // que tanto http://localhost:5173 como http://127.0.0.1:5173
    // funcionen sin depender de a cual resuelva "localhost" el sistema.
    host: true,
  },
});
