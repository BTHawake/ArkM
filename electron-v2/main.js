const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow = null;
let tray = null;
let backendProc = null;

const BACKEND_PORT = 8585;
const BACKEND_DIR = path.join(__dirname, '..', 'ArkM__', 'src');

// ---- 后端管理 ----

function startBackend() {
  return new Promise((resolve, reject) => {
    backendProc = spawn('python', [
      '-m', 'uvicorn', 'backend.server:app',
      '--host', 'localhost',
      '--port', String(BACKEND_PORT)
    ], {
      cwd: BACKEND_DIR,
      stdio: 'pipe'
    });

    backendProc.stderr.on('data', (data) => {
      const msg = data.toString();
      if (mainWindow) mainWindow.webContents.send('log', msg);
    });

    // 等待后端就绪
    let attempts = 0;
    const check = setInterval(async () => {
      attempts++;
      try {
        const http = require('http');
        await new Promise((res, rej) => {
          const req = http.get(`http://localhost:${BACKEND_PORT}/music/downloaded`, (resp) => {
            resp.resume(); res();
          });
          req.on('error', rej);
          req.setTimeout(2000, () => { req.destroy(); rej(new Error('timeout')); });
        });
        clearInterval(check);
        console.log('Backend ready');
        resolve();
      } catch {
        if (attempts > 30) { clearInterval(check); reject(new Error('Backend timeout')); }
      }
    }, 500);
  });
}

function stopBackend() {
  if (backendProc) {
    backendProc.kill();
    backendProc = null;
  }
}

// ---- 窗口 ----

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 750,
    minWidth: 900,
    minHeight: 600,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    icon: path.join(__dirname, 'assets', 'prts.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // 隐藏标题栏但仍可在 web 层拖动
  mainWindow.on('close', (event) => {
    if (tray) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

// ---- 托盘 ----

function createTray() {
  const icon = nativeImage.createFromPath(path.join(__dirname, 'assets', 'prts.ico'));
  tray = new Tray(icon.resize({ width: 16, height: 16 }));
  const contextMenu = Menu.buildFromTemplate([
    { label: '显示窗口', click: () => { mainWindow.show(); mainWindow.focus(); } },
    { type: 'separator' },
    { label: '退出', click: () => { tray = null; stopBackend(); app.quit(); } }
  ]);
  tray.setToolTip('ArkM');
  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => { mainWindow.show(); mainWindow.focus(); });
}

// ---- 生命周期 ----

app.whenReady().then(async () => {
  try {
    console.log('Starting backend...');
    await startBackend();
  } catch (e) {
    console.error('Backend failed to start:', e.message);
  }
  createWindow();
  createTray();
});

ipcMain.on('minimize-window', () => { if (mainWindow) mainWindow.minimize(); });

app.on('window-all-closed', () => {});
app.on('before-quit', () => { stopBackend(); });
