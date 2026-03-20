/**
 * Preload script — exposes safe IPC bridge to renderer
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronOrb', {
  moveWindow: (dx, dy) => ipcRenderer.send('move-window', { x: dx, y: dy }),
  minimize: () => ipcRenderer.send('minimize-orb'),
  quit: () => ipcRenderer.send('quit-orb'),
  openExternal: (url) => ipcRenderer.send('open-external', url),
});
