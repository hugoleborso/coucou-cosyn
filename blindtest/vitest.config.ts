import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    coverage: {
      include: ['lib/**/*.ts'],
      exclude: ['lib/**/*.test.ts', 'lib/blindtest-types.ts'],
      thresholds: { statements: 100, branches: 100, functions: 100, lines: 100 },
    },
  },
})
