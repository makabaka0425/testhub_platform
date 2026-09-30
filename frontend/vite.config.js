import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

const projectRoot = resolve(__dirname, '..')

const createConfig = (port, backendPort) => ({
  envDir: projectRoot,
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler', // 使用现代 Sass API
        silenceDeprecations: ['legacy-js-api'], // 静默旧警告
      },
    },
  },
  optimizeDeps: {
    esbuildOptions: {
      target: 'es2022',
    },
    force: true,
    exclude: ['tree-sitter'],
  },
  build: {
    target: 'es2022',
  },
  server: {
    port,
    host: '0.0.0.0',
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      Pragma: 'no-cache',
      Expires: '0',
    },
    proxy: {
      '^/api/': {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
        secure: false,
      },
      '^/media/': {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
        secure: false,
      },
      '^/app-automation-templates/': {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
        secure: false,
      },
      '^/app-automation-reports/': {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
        secure: false,
      },
      '^/ui-automation/allure-report-static/': {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
        rewrite: (path) =>
          path.replace(/^\/ui-automation/, '/api/ui-automation'),
        secure: false,
      },
      '^/ws/': {
        target: `ws://127.0.0.1:${backendPort}`,
        ws: true,
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', () => {})
          proxy.on('proxyReqWs', (proxyReq, req, socket) => {
            socket.on('error', () => {})
          })
        },
      },
    },
  },
  assetsInclude: ['**/*.wasm'],
})

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, projectRoot, '')
  const configuredPort = Number.parseInt(env.FRONTEND_DEV_PORT || '3001', 10)
  const configuredBackendPort = Number.parseInt(env.BACKEND_PORT || '8000', 10)
  const backendPort = Number.isNaN(configuredBackendPort) ? 8000 : configuredBackendPort

  return createConfig(Number.isNaN(configuredPort) ? 3001 : configuredPort, backendPort)
})
