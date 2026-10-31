/**
 * 布局与渲染深度审计（不依赖肉眼看图）。
 * 检查：图表是否真的画出来了（canvas 像素方差）、地图瓦片是否加载、
 * 文本是否被裁剪、面板是否重叠、关键对比度是否达标。
 */
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { mkdir, writeFile, rm } from 'node:fs/promises'
import { setTimeout as sleep } from 'node:timers/promises'

const BASE = process.argv[2] || 'http://127.0.0.1:5173'
const ROUTES = ['/overview', '/sites', '/peak', '/incidents', '/about']
const WIDTH = Number(process.argv[3] || 1440)
const THEME = process.argv[4] || 'dark'
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9334
const OUT = fileURLToPath(new URL('../../.probe/', import.meta.url))

await mkdir(OUT, { recursive: true })
const profile = OUT + 'profile2'
await rm(profile, { recursive: true, force: true })

const chrome = spawn(CHROME, [
  '--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-gpu', '--hide-scrollbars',
  '--force-device-scale-factor=1', 'about:blank'
], { stdio: 'ignore' })

async function getWs() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`)
      const j = await r.json()
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl
    } catch {}
    await sleep(250)
  }
  throw new Error('devtools unreachable')
}

const ws = new WebSocket(await getWs())
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })

let id = 0
const pending = new Map()
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) {
    const { res, rej } = pending.get(m.id); pending.delete(m.id)
    m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)
  }
}
const raw = (method, params = {}, sessionId) => new Promise((res, rej) => {
  const i = ++id
  pending.set(i, { res, rej })
  ws.send(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) }))
})

const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)

await S('Page.enable')
await S('Runtime.enable')
await S('Network.enable')
await S('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: 940, deviceScaleFactor: 1, mobile: false })

const EXPR = `(() => {
  const de = document.documentElement;
  const vw = de.clientWidth;

  // 1) canvas 是否真的画了东西：采样像素，算非底色比例
  const canvases = [...document.querySelectorAll('canvas')].map((c) => {
    let drawn = null;
    try {
      const ctx = c.getContext('2d');
      const w = c.width, h = c.height;
      const stepX = Math.max(1, Math.floor(w / 60));
      const stepY = Math.max(1, Math.floor(h / 60));
      const sample = ctx.getImageData(0, 0, w, h).data;
      let nonEmpty = 0, total = 0;
      for (let y = 0; y < h; y += stepY) {
        for (let x = 0; x < w; x += stepX) {
          const o = (y * w + x) * 4;
          total++;
          if (sample[o + 3] > 8) {
            const r = sample[o], g = sample[o + 1], b = sample[o + 2];
            if (r + g + b > 40) nonEmpty++;
          }
        }
      }
      drawn = total ? +(nonEmpty / total).toFixed(3) : null;
    } catch { drawn = 'tainted' }
    return { w: c.width, h: c.height, drawn };
  });

  // 2) 文本裁剪：scrollWidth > clientWidth + 2 且非滚动容器
  const clipped = [];
  document.querySelectorAll('h1,h2,h3,p,span,td,th,b,em,code,dt,dd,li').forEach((el) => {
    if (el.children.length) return;
    const t = (el.textContent || '').trim();
    if (!t) return;
    if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0) {
      const cs = getComputedStyle(el);
      if (cs.overflow === 'visible' && cs.textOverflow !== 'ellipsis') {
        clipped.push({ tag: el.tagName.toLowerCase(), cls: String(el.className).slice(0, 40), text: t.slice(0, 30), sw: el.scrollWidth, cw: el.clientWidth });
      }
    }
  });

  // 3) 面板重叠（同级 .panel / .kpi / .card 两两检查）
  const boxes = [...document.querySelectorAll('.panel, .kpi, .card')].map((el) => {
    const r = el.getBoundingClientRect();
    return { el, x: r.x, y: r.y, w: r.width, h: r.height };
  });
  const overlaps = [];
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
      const oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ox > 2 && oy > 2) {
        overlaps.push({
          a: a.el.className.toString().slice(0, 30),
          b: b.el.className.toString().slice(0, 30),
          ox: Math.round(ox), oy: Math.round(oy)
        });
      }
    }
  }

  // 4) 零高度/塌陷的面板
  const collapsed = boxes.filter((b) => b.w < 40 || b.h < 20).map((b) => ({
    cls: b.el.className.toString().slice(0, 40), w: Math.round(b.w), h: Math.round(b.h)
  }));

  // 5) 地图瓦片
  const tiles = document.querySelectorAll('.leaflet-tile-loaded').length;
  const mapBox = document.querySelector('.leaflet-container')?.getBoundingClientRect();

  // 6) 关键文字对比度（fg vs 实际背景）
  function lum(c) {
    const [r, g, b] = c.map((v) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }
  function parse(css) {
    const m = css.match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    const p = m[1].split(',').map((x) => parseFloat(x));
    return { rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1 };
  }
  function bgOf(el) {
    let n = el;
    while (n && n !== document.documentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0.85) return c.rgb;
      n = n.parentElement;
    }
    return parse(getComputedStyle(document.body).backgroundColor)?.rgb ?? [8, 11, 16];
  }
  const contrast = [];
  [['.main__note', 4.5], ['.panel__hint', 4.5], ['.kpi__label', 4.5], ['.card__loc', 4.5], ['.side-note', 4.5], ['.foot__meta', 4.5], ['.tag--sim', 4.5]].forEach(([sel, min]) => {
    const el = document.querySelector(sel);
    if (!el) return;
    const fg = parse(getComputedStyle(el).color);
    if (!fg) return;
    const bg = bgOf(el);
    const l1 = lum(fg.rgb), l2 = lum(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    contrast.push({ sel, ratio: +ratio.toFixed(2), pass: ratio >= min });
  });

  return {
    title: document.title,
    vw,
    overflowX: de.scrollWidth - vw,
    docHeight: de.scrollHeight,
    canvases,
    clippedCount: clipped.length,
    clipped: clipped.slice(0, 8),
    overlapCount: overlaps.length,
    overlaps: overlaps.slice(0, 5),
    collapsed,
    tiles,
    mapBox: mapBox ? { w: Math.round(mapBox.width), h: Math.round(mapBox.height) } : null,
    contrast
  };
})()`

const out = []
for (const route of ROUTES) {
  await S('Page.navigate', { url: BASE + route })
  await sleep(1200)
  // 用 localStorage 直接定主题，比"点按钮切换"稳（避免上一次点击把状态翻回去）
  await S('Runtime.evaluate', { expression: `localStorage.setItem('campusflow-theme', '${THEME}'); location.reload()` })
  await sleep(3200)
  const r = await S('Runtime.evaluate', { returnByValue: true, expression: EXPR })
  const shot = await S('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true })
  await writeFile(`${OUT}full${route.replace(/\//g, '')}-${WIDTH}-${THEME}.png`, Buffer.from(shot.data, 'base64'))
  out.push({ route, ...r.result.value })
}

await writeFile(OUT + `audit-${WIDTH}-${THEME}.json`, JSON.stringify(out, null, 2), 'utf-8')

for (const r of out) {
  console.log(`\n=== ${r.route} @${r.vw} ===`)
  console.log(`  overflowX=${r.overflowX} docH=${r.docHeight} canvas=${JSON.stringify(r.canvases)} tiles=${r.tiles} map=${JSON.stringify(r.mapBox)}`)
  console.log(`  clipped=${r.clippedCount} overlaps=${r.overlapCount} collapsed=${r.collapsed.length}`)
  for (const c of r.clipped) console.log('   CLIP', c.tag + '.' + c.cls, JSON.stringify(c.text), c.sw + '>' + c.cw)
  for (const o of r.overlaps) console.log('   OVER', o.a, '<->', o.b, o.ox + 'x' + o.oy)
  for (const c of r.collapsed) console.log('   TINY', c.cls, c.w + 'x' + c.h)
  for (const c of r.contrast) if (!c.pass) console.log('   CONTRAST', c.sel, c.ratio)
}

ws.close(); chrome.kill(); process.exit(0)
