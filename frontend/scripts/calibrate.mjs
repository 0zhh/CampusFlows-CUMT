/**
 * 校准面板回归：两种模式、真实拖拽、Esc 关闭、应用后落库、重开接着上次的值。
 * 全部走 CDP 真实事件，不调内部函数。
 */
import { spawn } from 'node:child_process'
import { mkdir, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'
import { tmpdir } from 'node:os'
import { join, sep } from 'node:path'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9900 + Math.floor(Math.random() * 60)
const OUT = join(tmpdir(), 'campusflow-probe') + sep
await mkdir(OUT, { recursive: true })
// clean-slate：每次跑之前清掉上一轮残留，避免临时目录越滚越大
await rm(OUT, { recursive: true, force: true }).catch(() => {})
await mkdir(OUT, { recursive: true }).catch(() => {})
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
const rows = () => ev("[...document.querySelectorAll('.cal__tbl tbody tr')].map(r => r.children[1].textContent + ',' + r.children[2].textContent).join('|')")
const click = async (x, y) => {
  await S('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 })
  await S('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 })
  await sleep(340)
}
const drag = async (x0, y0, x1, y1) => {
  await S('Input.dispatchMouseEvent', { type: 'mousePressed', x: x0, y: y0, button: 'left', clickCount: 1 })
  for (let i = 1; i <= 6; i++) {
    await S('Input.dispatchMouseEvent', { type: 'mouseMoved', x: x0 + ((x1 - x0) * i) / 6, y: y0 + ((y1 - y0) * i) / 6, button: 'left' })
    await sleep(60)
  }
  await S('Input.dispatchMouseEvent', { type: 'mouseReleased', x: x1, y: y1, button: 'left', clickCount: 1 })
  await sleep(420)
}
const esc = async () => {
  await S('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27, nativeVirtualKeyCode: 27 })
  await S('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27, nativeVirtualKeyCode: 27 })
  await sleep(600)
}
const openPanel = async () => {
  await ev("[...document.querySelectorAll('.icon-btn')].find(b => b.getAttribute('aria-label') === '校准站点位置').click()")
  await sleep(2400)
}
const mapRect = () => ev("(() => { const b = document.querySelector('.cal__map').getBoundingClientRect(); return { x: b.x, y: b.y, w: b.width, h: b.height } })()")

await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(3000)
await ev("localStorage.removeItem('campusflow-site-pos-v1'); localStorage.removeItem('campusflow-manual-bounds-v1'); location.reload()")
await sleep(3200)

// ---------- 1. 打开与默认态 ----------
const hasBtn = await ev("[...document.querySelectorAll('.icon-btn')].some(b => b.getAttribute('aria-label') === '校准站点位置')")
check('顶栏有校准按钮', hasBtn === true)
await openPanel()
check('校准面板打开', (await ev("!!document.querySelector('.cal')")) === true)
check('面板里有地图', (await ev("document.querySelectorAll('.cal__map.leaflet-container').length")) >= 1)
check('默认是对齐模式', (await ev("document.querySelector('.cal__mode-btn--on')?.textContent.includes('拖动')")) === true)
check('显示 4 行坐标', (await ev("document.querySelectorAll('.cal__tbl tbody tr').length")) === 4)

// ---------- 2. 真实拖拽 ----------
const r0 = await mapRect()
const before = await rows()
await drag(Math.round(r0.x + r0.w * 0.5), Math.round(r0.y + r0.h * 0.5), Math.round(r0.x + r0.w * 0.5 + 90), Math.round(r0.y + r0.h * 0.5 + 40))
const afterDrag = await rows()
check('拖拽原图后坐标改变', afterDrag !== before, before.split('|')[0] + ' -> ' + afterDrag.split('|')[0])

// ---------- 3. 缩放按钮 ----------
await ev("document.querySelectorAll('.cal__tools button')[0].click()")
await sleep(520)
const afterZoom = await rows()
check('点放大后坐标改变', afterZoom !== afterDrag, afterZoom.split('|')[0])

// ---------- 4. Esc 关闭 ----------
await esc()
check('Esc 关闭面板', (await ev("!!document.querySelector('.cal')")) === false)

// ---------- 5. 应用后落库且地图跟着动 ----------
await openPanel()
const pre = await rows()
await ev("[...document.querySelectorAll('.cal__acts .btn')].find(b => b.textContent.includes('应用')).click()")
await sleep(900)
check('应用后关闭面板', (await ev("!!document.querySelector('.cal')")) === false)
const stored = await ev("localStorage.getItem('campusflow-site-pos-v1')")
check('站点坐标写入 localStorage', !!stored && stored.includes('NH-TAOYUAN'), String(stored).slice(0, 70))
check('原图范围也一起写入', !!(await ev("localStorage.getItem('campusflow-manual-bounds-v1')")))
const markerPos = await ev("[...document.querySelectorAll('.site-marker')].map(m => m.style.transform).join('|')")
check('地图上 4 个标记已重绘', markerPos.split('|').length === 4, markerPos.slice(0, 60))

// ---------- 6. 刷新后仍在，且重开面板接着上次的值 ----------
await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(3000)
check('刷新后校准仍在', (await ev("localStorage.getItem('campusflow-site-pos-v1')")) === stored)
await openPanel()
const reopened = await rows()
check('重开面板接着上次的坐标', reopened === pre.split('|').map((s) => s).join('|'), reopened.split('|')[0] + ' vs ' + pre.split('|')[0])

// ---------- 7. 点选模式 ----------
await ev("document.querySelectorAll('.cal__mode-btn')[1].click()")
await sleep(700)
check('切到点选模式', (await ev("document.querySelector('.cal__mode-btn--on')?.textContent.includes('直接点')")) === true)
const pickedBefore = await rows()
const rr = await mapRect()
const pts = [[0.34, 0.28], [0.30, 0.58], [0.46, 0.52], [0.54, 0.78]]
for (const [fx, fy] of pts) await click(Math.round(rr.x + rr.w * fx), Math.round(rr.y + rr.h * fy))
const pickedAfter = await rows()
const pickedCount = await ev("document.querySelectorAll('.cal__tbl tbody tr').length")
check('点选后 4 行仍在', pickedCount === 4, pickedAfter)
check('点选坐标随点击变化', pickedAfter !== pickedBefore, pickedBefore.split('|')[0] + ' -> ' + pickedAfter.split('|')[0])
// 点选模式拖地图不应改坐标
const dragBase = await rows()
await drag(Math.round(rr.x + rr.w * 0.5), Math.round(rr.y + rr.h * 0.5), Math.round(rr.x + rr.w * 0.5 - 70), Math.round(rr.y + rr.h * 0.5 - 30))
const afterMapDrag = await rows()
check('点选模式拖地图不改坐标', afterMapDrag === dragBase, afterMapDrag.split('|')[0])
// 点选模式应用时不写原图范围
await ev("localStorage.removeItem('campusflow-manual-bounds-v1')")
await ev("[...document.querySelectorAll('.cal__acts .btn')].find(b => b.textContent.includes('应用')).click()")
await sleep(800)
check('点选模式不覆盖原图范围', (await ev("localStorage.getItem('campusflow-manual-bounds-v1')")) === null)

// ---------- 8. 重置 ----------
await openPanel()
await ev("[...document.querySelectorAll('.cal__acts .btn')].find(b => b.textContent.includes('重置')).click()")
await sleep(700)
check('重置后清掉 localStorage', (await ev("localStorage.getItem('campusflow-site-pos-v1')")) === null)
await esc()

// 收尾：清干净，别污染后面的截图
await ev("localStorage.removeItem('campusflow-site-pos-v1'); localStorage.removeItem('campusflow-manual-bounds-v1')")
console.log('\\n控制台错误:', errors.length, errors.slice(0, 3).join(' | '))
const pass = results.filter(Boolean).length
console.log(`结果: ${pass}/${results.length} 通过`)
ws.close(); chrome.kill(); process.exit(pass === results.length && errors.length === 0 ? 0 : 1)
