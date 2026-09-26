import { defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { spawn, ChildProcess } from 'child_process';
import net from 'net';
import path from 'path';

let loggedBackendWarning = false;
let backendAutoStarted = false;

function autoStartBackendPlugin(): Plugin {
  let backendProc: ChildProcess | null = null;

  return {
    name: 'auto-start-backend',
    configureServer(server) {
      const checkSocket = new net.Socket();
      checkSocket.setTimeout(600);

      const startBackend = () => {
        if (backendAutoStarted) return;
        backendAutoStarted = true;
        const rootDir = path.resolve(__dirname, '..');
        console.log('\n\x1b[36m%s\x1b[0m', '🚀 [WATERSCOPE] Backend not detected on :8000. Auto-starting Python backend...');

        backendProc = spawn('python', ['-m', 'uvicorn', 'api.app:app', '--host', '127.0.0.1', '--port', '8000', '--reload'], {
          cwd: rootDir,
          stdio: 'inherit',
          shell: true,
        });

        backendProc.on('error', (err) => {
          console.error('\x1b[31m%s\x1b[0m', `⚠️ [WATERSCOPE] Could not auto-start backend: ${err.message}`);
        });
      };

      checkSocket.on('connect', () => {
        checkSocket.destroy();
      });

      checkSocket.on('error', () => {
        checkSocket.destroy();
        startBackend();
      });

      checkSocket.on('timeout', () => {
        checkSocket.destroy();
        startBackend();
      });

      checkSocket.connect(8000, '127.0.0.1');

      const stopBackend = () => {
        if (backendProc && backendProc.pid) {
          try {
            if (process.platform === 'win32') {
              spawn('taskkill', ['/pid', backendProc.pid.toString(), '/t', '/f']);
            } else {
              backendProc.kill();
            }
          } catch {
            // ignore
          }
          backendProc = null;
        }
      };

      process.on('exit', stopBackend);
      process.on('SIGINT', () => {
        stopBackend();
        process.exit();
      });
      process.on('SIGTERM', () => {
        stopBackend();
        process.exit();
      });
      server.httpServer?.on('close', stopBackend);
    },
  };
}

export default defineConfig({
  plugins: [react(), autoStartBackendPlugin()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            if (!loggedBackendWarning) {
              if (backendAutoStarted) {
                console.warn('\x1b[33m%s\x1b[0m', '⏳ [WATERSCOPE] Backend is booting up on http://127.0.0.1:8000, requests will succeed momentarily...');
              } else {
                console.warn('\n\x1b[33m%s\x1b[0m', '⚠️  [WATERSCOPE] Python backend is not running on http://127.0.0.1:8000.');
                console.warn('\x1b[36m%s\x1b[0m\n', '👉 Start it with: python -m uvicorn api.app:app --port 8000 --reload (or run start.bat)\n');
              }
              loggedBackendWarning = true;
              setTimeout(() => { loggedBackendWarning = false; }, 8000);
            }
            if (res && !('headersSent' in res && (res as any).headersSent)) {
              (res as any).writeHead?.(503, { 'Content-Type': 'application/json' });
              (res as any).end?.(JSON.stringify({ error: 'Backend server not ready on port 8000' }));
            }
          });
        }
      },
      '/ml': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            if (res && !('headersSent' in res && (res as any).headersSent)) {
              (res as any).writeHead?.(503, { 'Content-Type': 'application/json' });
              (res as any).end?.(JSON.stringify({ error: 'Backend server not ready on port 8000' }));
            }
          });
        }
      }
    }
  }
});


