/**
 * 采集终版报告 / 答辩 PPT 用的界面截图。
 *
 * 用法：
 *   node report/tools/capture_shots.mjs               # 采全部页面（浅色 + 深色）
 *   node report/tools/capture_shots.mjs overview      # 只采某页
 *
 * 前提：前端 dev server 在 5173，后端在 8080（mysql profile），此时顶栏显示“接口数据”。
 * 产物：report/assets/shots/{name}-{theme}-{viewport|full}.png
 */
import { spawn } from 'node:child_process'
import { mkdir, writeFile, rm } from 'node:fs/promises'
import { setTimeout as sleep } from 'node:timers/promises'
import { tmpdir } from 'node:os'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const OUT = join(HERE, '..', 'assets', 'shots') + '\\'
await mkdir(OUT, { recursive: true })

const PAGES = [
  { route: '/overview', name: 'P1-overview' },
  { route: '/sites', name: 'P2-sites' },
  { route: '/peak', name: 'P3-peak', click: '松苑' },
  { route: '/incidents', name: 'P4-incidents' },
  { route: '/about', name: 'P5-about' },
  { route: '/overview', name: 'P1-map-expand', click: '放大' },
  { route: '/sites', name: 'P2-drawer', click: '打开详情抽屉' }
]
const only = process.argv[2]
const list = only ? PAGES.filter((p) => p.route.includes(only) || p.name.includes(only)) : PAGES

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9420 + Math.floor(Math.random() * 40)
const profile = join(tmpdir(), 'campusflow-capture') + PORT
await rm(profile, { recursive: true, force: true })

const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-gpu', '--hide-scrollbars',
  '--force-device-scale-factor=1', '--font-render-hinting=none', 'about:blank'], { stdio: 'ignore' })

async function getWs() {
  for (let i = 0; i < 100; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); const j = await r.json(); if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl } catch {}
    await sleep(200)
  }
  throw new Error('chrome devtools 未就绪')
}
const ws = new WebSocket(await getWs())
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })
let id = 0
const pending = new Map()
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result) }
}
const raw = (method, params = {}, sessionId) => new Promise((res, rej) => {
  const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) }))
})
const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)
await S('Page.enable'); await S('Runtime.enable')

async function shoot(route, name, theme, full, click) {
  await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false })
  await S('Page.navigate', { url: 'http://localhost:5173' + route })
  await sleep(900)
  await S('Runtime.evaluate', { expression: `localStorage.setItem('campusflow-theme','${theme}')` })
  await S('Page.reload')
  await sleep(4200)
  if (click) {
    await S('Runtime.evaluate', {
      expression: `[...document.querySelectorAll('button')].find(b => b.textContent.trim().startsWith(${JSON.stringify(click)}))?.click()`
    })
    await sleep(1200)
  }
  // 让进场动画与数字滚动跑完
  await S('Runtime.evaluate', { expression: 'window.scrollTo(0, document.body.scrollHeight); window.scrollTo(0,0)' })
  await sleep(900)
  const shot = await S('Page.captureScreenshot', { format: 'png', captureBeyondViewport: full })
  const file = `${OUT}${name}-${theme}-${full ? 'full' : 'view'}.png`
  await writeFile(file, Buffer.from(shot.data, 'base64'))
  console.log('saved', file)
}

for (const p of list) {
  await shoot(p.route, p.name, 'light', true, p.click)
  await shoot(p.route, p.name, 'light', false, p.click)
}
// 只采首页的深色版，用于封面/对比
if (!only) {
  await shoot('/overview', 'P1-overview', 'dark', true)
  await shoot('/overview', 'P1-overview', 'dark', false)
}

ws.close()
chrome.kill()
console.log('done')
process.exit(0)
