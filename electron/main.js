/**
 * Echo Sentinel — The Orb Desktop Widget
 * Electron main process
 *
 * Creates a transparent, frameless, always-on-top floating Orb.
 * Connects to the FastAPI server on localhost:8888.
 */

const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

let orbWindow = null;

function createOrbWindow() {
  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;

  orbWindow = new BrowserWindow({
    // Position: bottom-right corner by default
    x: sw - 340,
    y: sh - 460,

    width: 320,
    height: 440,

    // Transparent floating window
    transparent: true,
    frame: false,
    resizable: false,
    alwaysOnTop: true,
    hasShadow: false,
    vibrancy: 'ultra-dark',  // macOS only: blur behind window

    // Skip taskbar/dock
    skipTaskbar: false,
    titleBarStyle: 'hidden',

    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Load the widget page from the FastAPI server
  orbWindow.loadURL('http://localhost:8888/widget');

  // If server isn't running yet, load a fallback
  orbWindow.webContents.on('did-fail-load', () => {
    console.log('[Orb] Server not ready, retrying in 2s...');
    setTimeout(() => {
      orbWindow.loadURL('http://localhost:8888/widget');
    }, 2000);
  });

  // Dev tools in dev mode
  if (process.env.NODE_ENV === 'development') {
    orbWindow.webContents.openDevTools({ mode: 'detach' });
  }

  orbWindow.on('closed', () => { orbWindow = null; });
}

// ── IPC: window dragging ────────────────────────────────────────────────────
ipcMain.on('move-window', (event, { x, y }) => {
  if (orbWindow) {
    const [wx, wy] = orbWindow.getPosition();
    orbWindow.setPosition(wx + x, wy + y);
  }
});

ipcMain.on('minimize-orb', () => {
  if (orbWindow) orbWindow.hide();
});

ipcMain.on('quit-orb', () => {
  app.quit();
});

// ── App lifecycle ────────────────────────────────────────────────────────────
app.whenReady().then(createOrbWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (orbWindow === null) createOrbWindow();
});
