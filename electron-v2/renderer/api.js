// API client — 所有后端端点统一封装
const API = `http://localhost:${new URLSearchParams(location.search).get('port') || '8585'}`;

const api = {
  baseUrl: API,
  // 聚合视图（歌曲名 + 封面 URL 一次返回）
  async getAggregatedView(kind) {
    const r = await fetch(`${API}/view/${kind}`).catch(() => null);
    return r ? (await r.json().catch(() => ({}))).songs || [] : [];
  },

  // 下载（SSE 流）
  async downloadStream(name) {
    return fetch(`${API}/music/download`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ music_name: name }),
    });
  },

  // 删除
  async deleteMusic(name) {
    const r = await fetch(`${API}/music/delete`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ music_name: name }),
    });
    return r.json();
  },

  // 歌曲专辑信息
  async getAlbumInfo(name) {
    const r = await fetch(`${API}/music/${encodeURIComponent(name)}/album`).catch(() => null);
    if (!r || r.status === 404) return null;
    return r.json().catch(() => null);
  },

  // 封面图片 URL
  coverUrl(albumCid) { return `${API}/album/${albumCid}/cover`; },

  // 音频流 URL
  streamUrl(name) { return `${API}/stream/${encodeURIComponent(name)}`; },
};
