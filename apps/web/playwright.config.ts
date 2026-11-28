import { defineConfig, devices } from '@playwright/test'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const API_PORT = 18080
const WEB_PORT = 15173
const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')
const apiDir = resolve(rootDir, 'apps', 'api')
const protocolsSrc = resolve(rootDir, 'packages', 'diagnostic-protocols', 'src')

export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: `http://127.0.0.1:${WEB_PORT}`,
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `rm -f /tmp/diagnova-e2e.db && DATABASE_URL=sqlite:////tmp/diagnova-e2e.db JWT_SECRET=e2e-secret CORS_ORIGINS=http://127.0.0.1:${WEB_PORT},http://localhost:${WEB_PORT} SEED_ADMIN_EMAIL=admin@example.com SEED_ADMIN_PASSWORD=AdminDemo123! SEED_TECH_EMAIL=tech@example.com SEED_TECH_PASSWORD=TechDemo123! PYTHONPATH=${apiDir}:${protocolsSrc} python3 -m uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT}`,
      cwd: apiDir,
      url: `http://127.0.0.1:${API_PORT}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${WEB_PORT}`,
      url: `http://127.0.0.1:${WEB_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        VITE_API_URL: `http://127.0.0.1:${API_PORT}`,
      },
    },
  ],
})
