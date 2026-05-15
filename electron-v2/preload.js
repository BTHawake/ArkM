const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('arkm', {
  backendUrl: 'http://localhost:8585',
  minimize: () => ipcRenderer.send('minimize-window'),
});
