/**
 * 单独截取 P2 抽屉里的“.plan”（桃苑室内平面图），2 倍像素密度，供报告与 PPT 使用。
 * 产物：report/assets/figs/fig-plan.png
 */
import { spawn } from 'node:child_process'
import { mkdir, writeFile, rm } from 'node:fs/promises'
import { setTimeout as sleep } from 'node:timers/promises'
import { tmpdir } from 'node:os'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const OUT = join(HERE, '..', 'assets', 'figs', 'fig-plan.png')
await mkdir(dirname(OUT), { recursive: true })

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9470 + Math.floor(Math.random() * 20)
const profile = join(tmpdir(), 'campusflow-plan') + PORT
await rm(profile, { recursive: true, force: true })
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-gpu', '--hide-scrollbars',
  '--force-device-scale-factor=1', 'about:blank'], { stdio: 'ignore' })

async function getWs() {
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`)
      const j = await r.json()
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl
    } catch {}
    await sleep(200)
  }
  throw new Error('devtools 未就绪')
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
  const i = ++id
  pending.set(i, { res, rej })
  ws.send(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) }))
})
const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)
await S('Page.enable')
await S('Runtime.enable')
await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 2, mobile: false })

await S('Page.navigate', { url: 'http://localhost:5173/sites' })
await sleep(900)
await S('Runtime.evaluate', { expression: "localStorage.setItem('campusflow-theme','light')" })
await S('Page.reload')
await sleep(4000)
await S('Runtime.evaluate', {
  expression: "[...document.querySelectorAll('button')].find(b => b.textContent.includes('打开详情抽屉'))?.click()"
})
await sleep(2200)

const rect = await S('Runtime.evaluate', {
  expression: `(() => { const el = document.querySelector('.plan'); if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height } })()`,
  returnByValue: true
})
const box = rect.result.value
if (!box) throw new Error('没找到 .plan')
console.log('plan rect', box)

const shot = await S('Page.captureScreenshot', {
  format: 'png',
  captureBeyondViewport: true,
  clip: { x: box.x - 14, y: box.y - 14, width: box.w + 28, height: box.h + 56, scale: 2 }
})
await writeFile(OUT, Buffer.from(shot.data, 'base64'))
console.log('saved', OUT)
ws.close()
chrome.kill()
process.exit(0)
