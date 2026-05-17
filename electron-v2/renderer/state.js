// 渲染进程全局状态封装
const state = {
  viewId: 0,
  currentView: 0,
  playQueue: [],
  playHistory: [],
  downloadQueue: [],
  downloading: false,
  currentMusic: null,
  popupMode: 'cover',
};

// 竞态 token
state.nextViewId = () => ++state.viewId;
state.isStale = (id) => id !== state.viewId;

// 播放队列
state.enqueuePlay = (name) => {
  state.playQueue = state.playQueue.filter(n => n !== name);
  state.playQueue.unshift(name);
};
state.appendToQueue = (name) => { state.playQueue.push(name); };
state.dequeuePlay = () => state.playQueue.shift() || null;
state.hasQueueItems = () => state.playQueue.length > 0;

// 播放历史（最多 50 条）
state.recordPlay = (name) => {
  state.playHistory = state.playHistory.filter(n => n !== name);
  state.playHistory.unshift(name);
  if (state.playHistory.length > 50) state.playHistory.pop();
};
state.clearHistory = () => { state.playHistory = []; };

// 下载队列
state.enqueueDownload = (name) => { state.downloadQueue.push(name); };
state.dequeueDownload = () => state.downloadQueue.shift() || null;
state.hasDownloadQueue = () => state.downloadQueue.length > 0;
state.startDownloading = () => { state.downloading = true; };
state.stopDownloading = () => { state.downloading = false; };

// 当前播放
state.setCurrentMusic = (name) => { state.currentMusic = name; };
state.clearCurrentMusic = () => { state.currentMusic = null; };

// 弹出面板
state.setPopupMode = (mode) => { state.popupMode = mode; };
