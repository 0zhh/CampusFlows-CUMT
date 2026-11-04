import { spawn } from 'node:child_process'
import { rm } from 'node:fs/promises'
import { setTimeout as sleep } from 'node:timers/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9957
const profile = join(tmpdir(), 'campusflow-probe', 'lyprof')
await rm(profile, { recursive: true, force: true })
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, '--no-first-run', '--disable-gpu', 'about:blank'], { stdio: 'ignore' })
async function getWs() { for (let i = 0; i < 80; i++) { try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); const j = await r.json(); if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl } catch {} await sleep(200) } throw new Error('x') }
const ws = new WebSocket(await getWs())
await new Promise((r, j) => { ws.onopen = r; ws.onerror = j })
let id = 0; const pending = new Map(); const errors = []
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); return } if (m.method === 'Runtime.exceptionThrown') errors.push((m.params.exceptionDetails.exception?.description ?? '').slice(0, 140)) }
const raw = (method, params = {}, sid) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, ...(sid ? { sessionId: sid } : {}) })) })
const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)
await S('Page.enable'); await S('Runtime.enable')
await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 950, deviceScaleFactor: 1, mobile: false })
const ev = async (e) => { const r = await S('Runtime.evaluate', { returnByValue: true, awaitPromise: true, expression: e }); if (r.exceptionDetails) return 'ERR ' + (r.exceptionDetails.exception?.description ?? '').slice(0, 140); return r.result.value }
await S('Page.navigate', { url: 'http://127.0.0.1:5173/sites' })
await sleep(3600)
await ev("[...document.querySelectorAll('.chip,.site-card,.row,.site-row')].find(e=>e.textContent.includes('兰苑'))?.dispatchEvent(new MouseEvent('click',{bubbles:true}))")
await sleep(1600)
console.log('drawer:', await ev("!!document.querySelector('.drawer')"))
console.log('plan svg:', await ev("!!document.querySelector('.plan__svg')"))
console.log('racks:', await ev("document.querySelectorAll('.plan__svg .rack').length"))
console.log('zones:', await ev("[...document.querySelectorAll('.plan__svg .zone')].map(z=>z.getAttribute('class').replace('zone ','')).join('|')"))
console.log('meta:', await ev("document.querySelector('.plan__meta')?.textContent.replace(/\\s+/g,' ').trim()"))
console.log('empty note:', await ev("document.querySelector('.plan__empty')?.textContent.trim().slice(0,40)"))
console.log('errors:', errors.length, errors[0] || '')
ws.close(); chrome.kill(); process.exit(0)
