import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    tsconfigPaths: true,
  },
  test: {
    pool: "vmThreads",
    maxWorkers: 1,
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.{test,spec}.{ts,tsx}"],
    clearMocks: true,
    restoreMocks: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "json-summary"],
      reportsDirectory: "./coverage",
      thresholds: {
        statements: 40,
        branches: 35,
        functions: 30,
        lines: 40,
      },
      include: [
        "src/**/*.{ts,tsx}",
      ],
      exclude: [
        "src/**/*.d.ts",
        "src/**/types/**",
        "src/app/layout.tsx",
        "src/app/page.tsx",
      ],
    },
  },
});


