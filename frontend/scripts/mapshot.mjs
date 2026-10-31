import { spawn } from 'node:child_process'
import { mkdir, writeFile, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'

const WIDTH = Number(process.argv[2] || 1440)
const THEME = process.argv[3] || 'dark'
const LAYER = process.argv[4] || 'vector'
const NAME = process.argv[5] || 'mapshot'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9400 + Math.floor(Math.random() * 60)
const OUT = fileURLToPath(new URL('../../.probe/', import.meta.url))
await mkdir(OUT, { recursive: true })
const profile = OUT + 'mp-' + PORT
await rm(profile, { recursive: true, force: true })

const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-gpu', '--hide-scrollbars',
  '--force-device-scale-factor=1', 'about:blank'], { stdio: 'ignore' })

async function getWs() {
  for (let i = 0; i < 80; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); const j = await r.json(); if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl } catch {}
    await sleep(200)
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
await S('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: 1000, deviceScaleFactor: 1, mobile: false })
await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(1500)
if (THEME === 'light') { await S('Runtime.evaluate', { expression: "document.querySelector('.icon-btn')?.click()" }); await sleep(500) }
if (LAYER !== 'vector') {
  await S('Runtime.evaluate', { expression: `[...document.querySelectorAll('.layer-btn')].find(b => b.textContent.includes(${JSON.stringify(LAYER === 'satellite' ? '卫星' : '手册')}))?.click()` })
}
await sleep(4200)

const rect = await S('Runtime.evaluate', { returnByValue: true, expression: `(() => {
  const el = document.querySelector('.map-wrap') || document.querySelector('.leaflet-container');
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
})()` })
const { x, y, w, h } = rect.result.value
const shot = await S('Page.captureScreenshot', { format: 'png', clip: { x, y, width: w, height: h, scale: 1 }, captureBeyondViewport: true })
await writeFile(`${OUT}${NAME}.png`, Buffer.from(shot.data, 'base64'))
console.log('ok', `${OUT}${NAME}.png`, JSON.stringify(rect.result.value))
ws.close(); chrome.kill(); process.exit(0)
