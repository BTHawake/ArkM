// 频谱可视化引擎
class SpectrumEngine {
  constructor(canvasId, audioElement) {
    this.canvasId = canvasId;
    this.audio = audioElement;
    this.ctx = null;
    this.analyser = null;
    this.animId = null;
    this.sourceSet = false;
    this.error = null;
  }

  start() {
    try {
      if (!this.ctx || this.ctx.state === 'closed') {
        this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.ctx.createAnalyser();
        this.analyser.fftSize = 256;
        this.sourceSet = false;
      }
      if (this.ctx.state === 'suspended') this.ctx.resume();
      if (!this.sourceSet) {
        this.sourceSet = true;
        try {
          const src = this.ctx.createMediaElementSource(this.audio);
          src.connect(this.analyser); this.analyser.connect(this.ctx.destination);
        } catch (e) { /* 已存在 source */ }
      }
    } catch (e) { this.error = e; }

    if (this.animId) cancelAnimationFrame(this.animId);
    this._draw();
  }

  stop() {
    if (this.animId) { cancelAnimationFrame(this.animId); this.animId = null; }
    try {
      const c = document.getElementById(this.canvasId);
      if (c) { const ctx = c.getContext('2d'); if (ctx) ctx.clearRect(0, 0, c.width, c.height); }
    } catch {}
  }

  _draw() {
    if (!this.analyser) { this.animId = requestAnimationFrame(() => this._draw()); return; }
    const c = document.getElementById(this.canvasId);
    c.width = c.offsetWidth || 1200; c.height = c.offsetHeight || 80;
    const ctx2 = c.getContext('2d'), d = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(d);
    ctx2.clearRect(0, 0, c.width, c.height);
    const N = Math.min(d.length, 64), mid = c.width / 2, gap = 2, bw = Math.max((mid / N) - gap, 2);
    for (let i = 0; i < N; i++) {
      const h = (d[i] / 255) * c.height * 0.9;
      const g = ctx2.createLinearGradient(0, c.height - h, 0, c.height);
      g.addColorStop(0, '#00ffaa'); g.addColorStop(0.5, '#00cc88'); g.addColorStop(1, 'rgba(0,204,136,0.02)');
      ctx2.fillStyle = g;
      ctx2.fillRect(mid - (i + 1) * (bw + gap), c.height - h, bw, h);
      ctx2.fillRect(mid + i * (bw + gap), c.height - h, bw, h);
    }
    this.animId = requestAnimationFrame(() => this._draw());
  }
}
