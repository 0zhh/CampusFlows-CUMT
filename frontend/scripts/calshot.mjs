import { spawn } from 'node:child_process'
import { mkdir, rm, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'
import { tmpdir } from 'node:os'
import { join, sep } from 'node:path'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9950
const OUT = join(tmpdir(), 'campusflow-probe') + sep
await mkdir(OUT, { recursive: true })
// clean-slate：每次跑之前清掉上一轮残留，避免临时目录越滚越大
await rm(OUT, { recursive: true, force: true }).catch(() => {})
await mkdir(OUT, { recursive: true }).catch(() => {})
const profile = OUT + 'calshot'
await rm(profile, { recursive: true, force: true })
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1', 'about:blank'], { stdio: 'ignore' })
async function getWs() { for (let i = 0; i < 80; i++) { try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); const j = await r.json(); if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl } catch {} await sleep(200) } throw new Error('x') }
const ws = new WebSocket(await getWs())
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })
let id = 0; const pending = new Map()
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result) } }
const raw = (method, params = {}, sid) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, ...(sid ? { sessionId: sid } : {}) })) })
const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)
await S('Page.enable'); await S('Runtime.enable')
await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 950, deviceScaleFactor: 1, mobile: false })
await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(3000)
await S('Runtime.evaluate', { expression: "localStorage.removeItem('campusflow-site-pos-v1');location.reload()" })
await sleep(3200)
await S('Runtime.evaluate', { expression: "[...document.querySelectorAll('.icon-btn')].find(b=>b.getAttribute('aria-label')==='校准站点位置').click()" })
await sleep(2600)
const shot = await S('Page.captureScreenshot', { format: 'png' })
await writeFile(OUT + 'calpanel.png', Buffer.from(shot.data, 'base64'))
console.log('ok', OUT + 'calpanel.png')
ws.close(); chrome.kill()
// cleanup：删除本次用的浏览器 profile，避免临时目录越堆越大
await rm(profile, { recursive: true, force: true }).catch(() => {})
process.exit(0)
