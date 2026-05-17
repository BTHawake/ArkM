const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

const DEV_PORT = 8585;
const PKG_PORT = 8586;
const BACKEND_DIR = path.join(__dirname, '..', 'ArkM__', 'src');

class AppLifecycle {
  constructor() {
    this.mainWindow = null;
    this.tray = null;
    this.backendProc = null;
    this.isQuitting = false;
  }

  get port() { return app.isPackaged ? PKG_PORT : DEV_PORT; }

  // ---- 后端 ----

  startBackend() {
    const p = this.port;
    return new Promise((resolve, reject) => {
      let cmd, args, cwd;
      if (app.isPackaged) {
        cmd = path.join(process.resourcesPath, 'ark-backend', 'ark-backend.exe');
        args = []; cwd = process.resourcesPath;
      } else {
        cmd = 'python'; args = ['-m', 'uvicorn', 'backend.server:app', '--host', 'localhost', '--port', String(p)];
        cwd = BACKEND_DIR;
      }
      this.backendProc = spawn(cmd, args, { cwd, stdio: 'pipe' });
      let attempts = 0;
      const check = setInterval(async () => {
        attempts++;
        try {
          const http = require('http');
          await new Promise((res, rej) => {
            const req = http.get(`http://localhost:${p}/music/downloaded`, r => { r.resume(); res(); });
            req.on('error', rej); req.setTimeout(2000, () => { req.destroy(); rej(new Error('timeout')); });
          });
          clearInterval(check); console.log('Backend ready'); resolve();
        } catch { if (attempts > 30) { clearInterval(check); reject(new Error('Backend timeout')); } }
      }, 500);
    });
  }

  stopBackend() {
    if (this.backendProc) { this.backendProc.kill(); this.backendProc = null; }
  }

  // ---- 窗口 ----

  createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1200, height: 750, minWidth: 900, minHeight: 600,
      frame: false, transparent: true, backgroundColor: '#00000000',
      icon: path.join(__dirname, 'assets', 'prts.ico'),
      webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false }
    });

    this.mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'), { query: { port: String(this.port) } });
    this.mainWindow.on('restore', () => { this.mainWindow.setSkipTaskbar(false); });
  }

  // ---- 托盘 ----

  createTray() {
    const icon = nativeImage.createFromPath(path.join(__dirname, 'assets', 'prts.ico'));
    this.tray = new Tray(icon.resize({ width: 16, height: 16 }));
    const ctx = this;
    const menu = Menu.buildFromTemplate([
      { label: '显示窗口', click: () => { if (ctx.mainWindow && !ctx.mainWindow.isDestroyed()) { ctx.mainWindow.setSkipTaskbar(false); ctx.mainWindow.restore(); ctx.mainWindow.show(); ctx.mainWindow.focus(); } } },
      { type: 'separator' },
      { label: '退出', click: () => { ctx.isQuitting = true; ctx.tray.destroy(); ctx.tray = null; ctx.stopBackend(); app.quit(); } }
    ]);
    this.tray.setToolTip('ArkM');
    this.tray.setContextMenu(menu);
    this.tray.on('double-click', () => { if (ctx.mainWindow && !ctx.mainWindow.isDestroyed()) { ctx.mainWindow.setSkipTaskbar(false); ctx.mainWindow.restore(); ctx.mainWindow.show(); ctx.mainWindow.focus(); } });
  }

  // ---- 启动 ----

  async run() {
    try { console.log('Starting backend...'); await this.startBackend(); }
    catch (e) { console.error('Backend failed:', e.message); }
    this.createWindow();
    this.createTray();
  }
}

const lifecycle = new AppLifecycle();

app.whenReady().then(() => lifecycle.run());

ipcMain.on('minimize-window', () => { if (lifecycle.mainWindow) lifecycle.mainWindow.minimize(); });
ipcMain.on('hide-window', () => {
    if (!lifecycle.mainWindow || lifecycle.mainWindow.isDestroyed()) return;
    lifecycle.mainWindow.setSkipTaskbar(true);
    lifecycle.mainWindow.minimize();
  });

app.on('window-all-closed', () => {});
app.on('before-quit', () => { lifecycle.stopBackend(); });
