const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('arkm', {
  minimize: () => ipcRenderer.send('minimize-window'),
  hide: () => ipcRenderer.send('hide-window'),
});
