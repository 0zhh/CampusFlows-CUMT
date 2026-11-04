import { spawn } from 'node:child_process'
import { mkdir, writeFile, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'
import { tmpdir } from 'node:os'
import { join, sep } from 'node:path'

const BASE = 'http://127.0.0.1:5173'
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9335
const OUT = join(tmpdir(), 'campusflow-probe') + sep
await mkdir(OUT, { recursive: true })
// clean-slate：每次跑之前清掉上一轮残留，避免临时目录越滚越大
await rm(OUT, { recursive: true, force: true }).catch(() => {})
await mkdir(OUT, { recursive: true }).catch(() => {})
const profile = OUT + 'profile3'
await rm(profile, { recursive: true, force: true })

const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-gpu', '--hide-scrollbars',
  '--force-device-scale-factor=1', 'about:blank'], { stdio: 'ignore' })

async function getWs() {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); const j = await r.json(); if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl } catch {}
    await sleep(250)
  }
  throw new Error('no devtools')
}
const ws = new WebSocket(await getWs())
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })
let id = 0; const pending = new Map()
ws.onmessage = (ev) => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result) } }
const raw = (method, params = {}, sessionId) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) })) })
const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)
await S('Page.enable'); await S('Runtime.enable')
await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 940, deviceScaleFactor: 1, mobile: false })
await S('Page.navigate', { url: BASE + '/overview' })
await sleep(4500)

const r = await S('Runtime.evaluate', { returnByValue: true, expression: `(() => {
  const map = document.querySelector('.leaflet-container');
  const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')];
  const fills = {};
  paths.forEach((p) => { const f = p.getAttribute('fill') || 'none'; fills[f] = (fills[f] || 0) + 1 });
  const b = map?.getBoundingClientRect();
  const svg = document.querySelector('.leaflet-overlay-pane svg');
  return {
    mapBox: b ? { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) } : null,
    pathCount: paths.length,
    fills,
    svgBox: svg ? { w: svg.getAttribute('width'), h: svg.getAttribute('height'), viewBox: svg.getAttribute('viewBox') } : null,
    markers: [...document.querySelectorAll('.site-marker')].map((m) => {
      const rc = m.getBoundingClientRect();
      return { x: Math.round(rc.x), y: Math.round(rc.y), w: Math.round(rc.width) };
    }),
    computedBg: getComputedStyle(map).backgroundColor,
    attribution: document.querySelector('.leaflet-control-attribution')?.innerText
  };
})()` })
console.log(JSON.stringify(r.result.value, null, 2))

const shot = await S('Page.captureScreenshot', { format: 'png' })
await writeFile(OUT + 'map.png', Buffer.from(shot.data, 'base64'))

ws.close(); chrome.kill()
// cleanup：删除本次用的浏览器 profile，避免临时目录越堆越大
await rm(profile, { recursive: true, force: true }).catch(() => {})
process.exit(0)
