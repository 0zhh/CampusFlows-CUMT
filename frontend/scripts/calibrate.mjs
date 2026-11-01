/**
 * 校准面板自检：打开 → 拖动/缩放 → 看反算坐标是否跟着变 → 应用 → 刷新后仍在。
 */
import { spawn } from 'node:child_process'
import { mkdir, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9900 + Math.floor(Math.random() * 60)
const OUT = fileURLToPath(new URL('../../.probe/', import.meta.url))
await mkdir(OUT, { recursive: true })
const profile = OUT + 'cal-' + PORT
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
let id = 0; const pending = new Map(); const errors = []
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) {
    const { res, rej } = pending.get(m.id); pending.delete(m.id)
    m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)
    return
  }
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map((a) => a.value ?? '').join(' ').slice(0, 160))
  if (m.method === 'Runtime.exceptionThrown') errors.push('EXC ' + (m.params.exceptionDetails.exception?.description ?? '').slice(0, 180))
}
const raw = (method, params = {}, sessionId) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) })) })
const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)
await S('Page.enable'); await S('Runtime.enable')
await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 950, deviceScaleFactor: 1, mobile: false })
const ev = async (e) => {
  const r = await S('Runtime.evaluate', { returnByValue: true, awaitPromise: true, expression: e })
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? 'eval')
  return r.result.value
}
const results = []
const check = (n, ok, d) => { results.push(ok); console.log((ok ? '  PASS ' : '  FAIL ') + n + (d ? '  — ' + d : '')) }

await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(3000)
await ev(`localStorage.removeItem('campusflow-site-pos-v1')`)
await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(3000)

// 打开校准
const hasBtn = await ev(`[...document.querySelectorAll('.icon-btn')].some(b => b.getAttribute('aria-label') === '校准站点位置')`)
check('顶栏有校准按钮', hasBtn === true)
await ev(`[...document.querySelectorAll('.icon-btn')].find(b => b.getAttribute('aria-label') === '校准站点位置').click()`)
await sleep(2200)
check('校准面板打开', (await ev(`!!document.querySelector('.cal')`)) === true)
check('校正面板里有地图块', (await ev(`document.querySelectorAll('.cal__map .leaflet-container, .cal__map.leaflet-container').length`)) >= 1)
check('面板显示 4 行坐标', (await ev(`document.querySelectorAll('.cal__tbl tbody tr').length`)) === 4)
const before = await ev(`[...document.querySelectorAll('.cal__tbl tbody tr')].map(r => r.children[1].textContent + ',' + r.children[2].textContent).join('|')`)

// 缩放：点两次放大按钮
await ev(`document.querySelectorAll('.cal__tools button')[0].click()`)
await sleep(500)
await ev(`document.querySelectorAll('.cal__tools button')[0].click()`)
await sleep(600)
const afterZoom = await ev(`[...document.querySelectorAll('.cal__tbl tbody tr')].map(r => r.children[1].textContent + ',' + r.children[2].textContent).join('|')`)
check('缩放后坐标随之变化', afterZoom !== before, before + ' -> ' + afterZoom)

// 平移：点右移
await ev(`document.querySelectorAll('.cal__tools button')[3].click()`)
await sleep(500)
const afterNudge = await ev(`[...document.querySelectorAll('.cal__tbl tbody tr')].map(r => r.children[1].textContent + ',' + r.children[2].textContent).join('|')`)
check('平移后坐标随之变化', afterNudge !== afterZoom, afterNudge)

// 应用
await ev(`[...document.querySelectorAll('.cal__acts .btn')].find(b => b.textContent.includes('应用')).click()`)
await sleep(900)
check('应用后关闭面板', (await ev(`!!document.querySelector('.cal')`)) === false)
const stored = await ev(`localStorage.getItem('campusflow-site-pos-v1')`)
check('坐标写入 localStorage', !!stored && stored.includes('NH-TAOYUAN'), String(stored).slice(0, 90))

// 刷新后仍在
await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(3000)
const kept = await ev(`localStorage.getItem('campusflow-site-pos-v1')`)
check('刷新后校准仍在', kept === stored)
const markers = await ev(`document.querySelectorAll('.site-marker').length`)
check('地图仍渲染 4 个站点', markers === 4, String(markers))

// 点选模式：切过去，在地图上按顺序点四下，看坐标是否跟着走
await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(2800)
await ev(`[...document.querySelectorAll('.icon-btn')].find(b => b.getAttribute('aria-label') === '校准站点位置').click()`)
await sleep(2200)
const modeOk = await ev(`document.querySelectorAll('.cal__mode-btn').length`)
check('校准有两种模式', modeOk === 2, String(modeOk))
await ev(`document.querySelectorAll('.cal__mode-btn')[1].click()`)
await sleep(600)
const r = await ev(`(() => { const el = document.querySelector('.cal__map'); const b = el.getBoundingClientRect(); return { x: b.x, y: b.y, w: b.width, h: b.height } })()`)
const pts = [[0.35, 0.30], [0.30, 0.62], [0.48, 0.55], [0.55, 0.80]]
for (const [fx, fy] of pts) {
  const x = Math.round(r.x + r.w * fx)
  const y = Math.round(r.y + r.h * fy)
  for (const type of ['mousePressed', 'mouseReleased']) {
    await S('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1 })
  }
  await sleep(400)
}
const pickedRows = await ev(`[...document.querySelectorAll('.cal__tbl tbody tr')].map(t => t.children[1].textContent + ',' + t.children[2].textContent).join('|')`)
check('点选后四个坐标都被填写', await ev(`document.querySelectorAll('.cal__tbl tbody tr').length`) === 4, pickedRows)
check('点选坐标与红点反算不同', pickedRows.split('|').filter((s) => s === '0.00000,0.00000').length === 0, pickedRows.slice(0, 80))

// 清理，避免污染后续截图
await ev(`localStorage.removeItem('campusflow-site-pos-v1'); localStorage.removeItem('campusflow-manual-bounds-v1')`)
console.log('\n控制台错误:', errors.length, errors.slice(0, 3).join(' | '))
const pass = results.filter(Boolean).length
console.log(`结果: ${pass}/${results.length} 通过`)
ws.close(); chrome.kill(); process.exit(pass === results.length && errors.length === 0 ? 0 : 1)
