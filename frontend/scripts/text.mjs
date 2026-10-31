import { spawn } from 'node:child_process'
import { mkdir, writeFile, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'

const ROUTE = process.argv[2] || '/overview'
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9500 + Math.floor(Math.random() * 60)
const OUT = fileURLToPath(new URL('../../.probe/', import.meta.url))
await mkdir(OUT, { recursive: true })
const profile = OUT + 'tx-' + PORT
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
await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 950, deviceScaleFactor: 1, mobile: false })
await S('Page.navigate', { url: 'http://127.0.0.1:5173' + ROUTE })
await sleep(4000)
const SC = process.argv[3]
if (SC) {
  await S('Runtime.evaluate', { expression: `[...document.querySelectorAll('.picker__tab')].find((b) => b.textContent.includes(${JSON.stringify(SC)}))?.click()` })
  await sleep(2000)
}
const r = await S('Runtime.evaluate', { returnByValue: true, expression: 'document.querySelector("main").innerText' })
console.log(r.result.value)
ws.close(); chrome.kill(); process.exit(0)
