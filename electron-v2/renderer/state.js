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
