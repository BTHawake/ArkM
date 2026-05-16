const API = window.arkm?.backendUrl || 'http://localhost:8585';
const audio = document.getElementById('audio-player');

let currentView = 0;       // 0=undownloaded, 1=music
let playQueue = [];
let currentMusic = null;
let popupMode = 'cover';   // 'cover' | 'queue'

// ---- 工具 ----

function log(msg) {
  const el = document.getElementById('log-output');
  const now = new Date().toLocaleTimeString();
  el.textContent += `[${now}] ${msg}\n`;
  el.scrollTop = el.scrollHeight;
}

let _loadToken = 0;  // 竞态防护 token

async function loadCoverGrid() {
  const token = ++_loadToken;
  const grid = document.getElementById('cover-grid');
  grid.innerHTML = '';

  const kind = currentView === 0 ? 'undownloaded' : 'downloaded';
  const resp = await fetch(`${API}/view/${kind}`).catch(() => null);
  if (!resp || token !== _loadToken) return;
  const data = await resp.json().catch(() => ({}));
  const songs = data.songs || [];
  if (token !== _loadToken) return;

  log(`${currentView === 0 ? '待下载' : '已下载'}: ${songs.length} 首`);

  for (const item of songs) {
    if (token !== _loadToken) return;
    const name = item.name;

    const card = document.createElement('div');
    card.className = 'cover-card';
    card.title = name;

    const imgHtml = item.cover_url
      ? `<img src="${API}${item.cover_url}" onerror="this.parentElement.innerHTML='<div class=card-placeholder>🎵</div>'">`
      : '<div class="card-placeholder">🎵</div>';

    card.innerHTML = imgHtml + `<div class="card-name">${name}</div>`;
    card.addEventListener('dblclick', () => { if (currentView === 0) downloadMusic(name); else playMusic(name); });
    card.addEventListener('contextmenu', (e) => { e.preventDefault(); showContextMenu(e.clientX, e.clientY, name); });
    grid.appendChild(card);
  }
}

// ---- 下载 ----

async function downloadMusic(name) {
  if (!confirm(`确定下载《${name}》吗？`)) return;
  log(`开始下载: ${name}`);

  try {
    const resp = await fetch(`${API}/music/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ music_name: name }),
    });
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const d = JSON.parse(line.slice(6));
          if (d.type === 'progress') {
            document.getElementById('log-output').lastChild && (document.getElementById('log-output').lastChild.textContent = `下载: ${d.filename} ${(d.downloaded / d.total * 100).toFixed(1)}%`);
          } else if (d.type === 'result') {
            log(d.message);
            loadCoverGrid();
          }
        }
      }
    }
  } catch (e) {
    log(`下载失败: ${e.message}`);
  }
}

// ---- 删除 ----

async function deleteMusic(name) {
  if (!confirm(`确定删除《${name}》？此操作不可撤销！`)) return;
  try {
    const resp = await fetch(`${API}/music/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ music_name: name }),
    });
    const data = await resp.json();
    log(data.message);
    loadCoverGrid();
  } catch (e) {
    log(`删除失败: ${e.message}`);
  }
}

// ---- 播放 ----

function playMusic(name) {
  playQueue = playQueue.filter(n => n !== name);
  playQueue.unshift(name);
  playNext();
}

function playNext() {
  if (playQueue.length === 0) { currentMusic = null; return; }
  currentMusic = playQueue.shift();
  audio.src = `${API}/stream/${encodeURIComponent(currentMusic)}`;
  audio.load();
  audio.play().catch(e => log(`播放失败: ${e.message}`));
  document.getElementById('popup-song-title').textContent = currentMusic;
  updatePopupCover(currentMusic);
  updateQueueUI();
  log(`正在播放: ${currentMusic}`);
}

function togglePlayPause() {
  if (!currentMusic) { log('请先选择歌曲'); return; }
  audio.paused ? audio.play() : audio.pause();
}

function updatePopupCover(name) {
  fetch(`${API}/music/${encodeURIComponent(name)}/album`)
    .then(r => r.json())
    .then(a => {
      if (a && a.album_cid) {
        document.getElementById('popup-cover').src = `${API}/album/${a.album_cid}/cover`;
        document.getElementById('bar-cover-btn').style.backgroundImage =
          `url(${API}/album/${a.album_cid}/cover)`;
      }
    }).catch(() => {});
}

function updateQueueUI() {
  const list = document.getElementById('popup-queue-list');
  list.innerHTML = playQueue.map((name, i) =>
    `<li class="${name === currentMusic ? 'current' : ''}" onclick="clickQueueItem('${name}')">${name}</li>`
  ).join('');
}

window.clickQueueItem = (name) => {
  playQueue = playQueue.filter(n => n !== name);
  playQueue.unshift(name);
  playNext();
};

// ---- 弹出面板 ----

function togglePopup(mode) {
  const panel = document.getElementById('popup-panel');
  if (popupMode === mode && panel.classList.contains('open')) {
    panel.classList.remove('open');
    return;
  }
  popupMode = mode;

  if (mode === 'cover') {
    document.getElementById('popup-cover-area').style.display = '';
    document.getElementById('popup-queue-list').style.display = 'none';
    if (currentMusic) updatePopupCover(currentMusic);
  } else {
    document.getElementById('popup-cover-area').style.display = 'none';
    document.getElementById('popup-queue-list').style.display = '';
    updateQueueUI();
  }
  panel.classList.add('open');
}

// ---- 初始化 ----

document.addEventListener('DOMContentLoaded', () => {
  // 搜索
  document.getElementById('search-input').addEventListener('input', (e) => {
    const kw = e.target.value.toLowerCase();
    document.querySelectorAll('.cover-card').forEach(card => {
      card.style.display = kw ? (
        card.querySelector('.card-name')?.textContent.toLowerCase().includes(kw) ? '' : 'none'
      ) : '';
    });
  });

  // 侧栏导航 — 用 mousedown 避免 click 延迟
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('mousedown', (e) => {
      e.preventDefault();
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentView = parseInt(btn.dataset.view);
      document.getElementById('search-input').value = '';
      loadCoverGrid();
    });
  });

  // 播放条按钮
  document.getElementById('btn-play').addEventListener('click', togglePlayPause);
  document.getElementById('btn-pause').addEventListener('click', () => {
    audio.pause(); audio.currentTime = 0;
    log('已停止');
    currentMusic = null;
    document.getElementById('popup-song-title').textContent = '';
    document.getElementById('progress-bar').value = 0;
    document.getElementById('time-label').textContent = '00:00 / 00:00';
  });

  // 进度条
  const progressBar = document.getElementById('progress-bar');
  progressBar.addEventListener('input', () => {
    if (audio.duration) audio.currentTime = (progressBar.value / 1000) * audio.duration;
  });

  // 音量
  document.getElementById('volume-bar').addEventListener('input', (e) => {
    audio.volume = e.target.value / 100;
  });
  audio.volume = 0.5;
  document.getElementById('volume-bar').value = 50;

  // 播放结束自动下一首
  audio.addEventListener('ended', () => {
    isPlaying = false;
    playNext();
  });

  // 进度更新
  audio.addEventListener('timeupdate', () => {
    if (audio.duration) {
      const pct = (audio.currentTime / audio.duration) * 100;
      document.getElementById('progress-bar').value = (audio.currentTime / audio.duration) * 1000;
      document.getElementById('progress-bar').style.setProperty('--progress', pct + '%');
      const c = new Date(audio.currentTime * 1000).toISOString().slice(14, 19);
      const t = new Date(audio.duration * 1000).toISOString().slice(14, 19);
      document.getElementById('time-label').textContent = `${c} / ${t}`;
    }
  });

  // 播放/暂停时切换脉冲动画 + 图标
  const playIcon = document.querySelector('#btn-play i');
  audio.addEventListener('play', () => {
    document.getElementById('btn-play').classList.add('playing');
    if (playIcon) playIcon.textContent = 'pause';
  });
  audio.addEventListener('pause', () => {
    document.getElementById('btn-play').classList.remove('playing');
    if (playIcon) playIcon.textContent = 'play_arrow';
  });

  // 弹出面板
  document.getElementById('bar-cover-btn').addEventListener('click', () => togglePopup('cover'));
  document.getElementById('bar-queue-btn').addEventListener('click', () => togglePopup('queue'));

  // 日志
  document.getElementById('log-toggle').addEventListener('click', () => {
    const panel = document.getElementById('log-panel');
    const icon = document.querySelector('#log-toggle i');
    panel.classList.toggle('collapsed');
    if (icon) icon.textContent = panel.classList.contains('collapsed') ? 'chevron_left' : 'chevron_right';
  });
  document.getElementById('log-clear').addEventListener('click', () => {
    document.getElementById('log-output').textContent = '';
  });

  // 窗口控制
  document.getElementById('min-btn').addEventListener('click', () => {
    if (window.arkm && window.arkm.minimize) window.arkm.minimize();
  });
  document.getElementById('close-btn').addEventListener('click', () => window.close());
  document.getElementById('close-btn').addEventListener('click', () => {
    window.close();
  });

  // 初始加载
  loadCoverGrid();
  log('ArkM 初始化完成');

  // 点菜单外的空白关闭右键菜单
  setTimeout(() => {
    document.addEventListener('click', (ev) => {
      if (!ev.target.closest('#ctx-menu')) {
        const m = document.getElementById('ctx-menu');
        if (m) m.remove();
      }
    }, true);
  }, 0);
});

// ---- 右键菜单 ----

let _ctxTarget = null;

function showContextMenu(x, y, name) {
  _ctxTarget = name;
  const old = document.getElementById('ctx-menu');
  if (old) old.remove();

  const menu = document.createElement('div');
  menu.id = 'ctx-menu';
  Object.assign(menu.style, {
    position: 'fixed', left: x + 'px', top: y + 'px',
    background: 'rgba(35,35,35,0.95)', border: '1px solid #555',
    borderRadius: '6px', padding: '4px 0', minWidth: '140px',
    zIndex: '9999', backdropFilter: 'blur(6px)', animation: 'fadeIn 0.15s ease',
  });
  menu.addEventListener('click', (e) => e.stopPropagation());

  const items = [];
  if (currentView === 0) {
    items.push({ label: '⬇ 下载', action: () => downloadMusic(name) });
  } else {
    items.push({ label: '▶ 播放', action: () => playMusic(name) });
    items.push({ label: '📋 加入队列', action: () => { playQueue.push(name); updateQueueUI(); log(`已加入队列: ${name}`); } });
    items.push({ type: 'sep' });
    items.push({ label: '🗑 删除', action: () => deleteMusic(name) });
  }

  for (const item of items) {
    if (item.type === 'sep') {
      const sep = document.createElement('div');
      sep.style.cssText = 'height:1px;background:#444;margin:4px 8px;';
      menu.appendChild(sep);
    } else {
      const el = document.createElement('div');
      el.textContent = item.label;
      el.style.cssText = 'padding:8px 14px;font-size:13px;color:#ccc;cursor:pointer;transition:background 0.1s;';
      el.addEventListener('mouseenter', () => { el.style.background = 'rgba(80,80,80,0.5)'; el.style.color = '#fff'; });
      el.addEventListener('mouseleave', () => { el.style.background = ''; el.style.color = '#ccc'; });
      el.addEventListener('click', (e) => { e.stopPropagation(); item.action(); menu.remove(); });
      menu.appendChild(el);
    }
  }

  document.body.appendChild(menu);
}
