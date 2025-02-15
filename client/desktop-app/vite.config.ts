import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

// Use POCKET_GITHUB_PATH if available; otherwise, use a relative fallback.
const outDir = process.env.POCKET_GITHUB_PATH
  ? path.join(process.env.POCKET_GITHUB_PATH, "dist/client/desktop-app/react")
  : "../../../dist/client/desktop-app/react";

// export default defineConfig({
//   build: {
//     outDir: '../dist',
//   },
//   plugins: [react()]
// }); 


// https://vitejs.dev/config/
export default defineConfig(() => ({
  root: 'react/src',
  plugins: [react()],
  build: {
    outDir: outDir,
    emptyOutDir: true,
  },

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      ignored: ["**/rust-tauri/**", "**/installer/**", "**/local-env/**"],
    },
  },
}));
