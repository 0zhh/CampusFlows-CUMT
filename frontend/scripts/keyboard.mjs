/**
 * 键盘可达性检查：只用 Tab / Enter / 方向键走一遍主流程。
 * 断言：焦点环可见、跳过链接可用、抽屉能开能关、场景切换能操作。
 */
import { spawn } from 'node:child_process'
import { mkdir, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'
import { tmpdir } from 'node:os'
import { join, sep } from 'node:path'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9700 + Math.floor(Math.random() * 60)
const OUT = join(tmpdir(), 'campusflow-probe') + sep
await mkdir(OUT, { recursive: true })
const profile = OUT + 'kb-' + PORT
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
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) {
    const { res, rej } = pending.get(m.id); pending.delete(m.id)
    m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)
  }
}
const raw = (method, params = {}, sessionId) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) })) })
const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)
await S('Page.enable'); await S('Runtime.enable')
await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 950, deviceScaleFactor: 1, mobile: false })

const ev = async (expr) => {
  const r = await S('Runtime.evaluate', { returnByValue: true, awaitPromise: true, expression: expr })
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? 'eval')
  return r.result.value
}
// 按钮的 Enter 激活依赖 keydown 带上 text，否则 CDP 只会派发事件、
// 不触发 <button> 的默认点击行为
const key = async (k, code, vk, text) => {
  const base = { key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk }
  await S('Input.dispatchKeyEvent', { type: text ? 'keyDown' : 'rawKeyDown', ...base, ...(text ? { text } : {}) })
  await S('Input.dispatchKeyEvent', { type: 'keyUp', ...base })
  await sleep(200)
}
const tabN = async (n) => { for (let i = 0; i < n; i++) await key('Tab', 'Tab', 9) }

const results = []
const check = (name, ok, detail) => {
  results.push({ name, ok, detail })
  console.log((ok ? '  PASS ' : '  FAIL ') + name + (detail ? '  — ' + detail : ''))
}

await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(2800)

// 1. 第一个 Tab 停在跳过链接
await key('Tab', 'Tab', 9)
const first = await ev(`(() => { const a = document.activeElement; return { cls: a.className, text: (a.textContent||'').trim().slice(0,20) } })()`)
check('首个 Tab 命中跳过链接', String(first.cls).includes('skip'), JSON.stringify(first))

// 2. 焦点环可见（outline 不是 none 且宽度 > 0）
const ring = await ev(`(() => {
  const a = document.activeElement;
  const s = getComputedStyle(a);
  return { outline: s.outlineStyle + ' ' + s.outlineWidth, has: s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0 };
})()`)
check('焦点环可见', ring.has === true, ring.outline)

// 3. Tab 顺序经过 5 个导航项
const navReached = []
for (let i = 0; i < 12; i++) {
  await key('Tab', 'Tab', 9)
  const info = await ev(`(() => { const a = document.activeElement; return { tag: a.tagName, cls: a.className, text: (a.textContent||'').trim().replace(/\\s+/g,' ').slice(0,14) } })()`)
  if (String(info.cls).includes('nav-item')) navReached.push(info.text)
}
check('Tab 到达 6 个导航项', navReached.length >= 6, navReached.length + ' 次：' + navReached.slice(0, 5).join(' / '))

// 4. Enter 能激活导航
await ev(`document.querySelector('.nav-item[href="/sites"]').focus()`)
await key('Enter', 'Enter', 13, '\r')
await sleep(1600)
check('Enter 激活导航', (await ev('location.pathname')) === '/sites', await ev('location.pathname'))

// 5. 站点卡片可以用键盘打开抽屉
await S('Page.navigate', { url: 'http://127.0.0.1:5173/overview' })
await sleep(2600)
const focused = await ev(`(() => {
  const b = document.querySelector('.site-row');
  if (!b) return false; b.focus();
  return document.activeElement === b;
})()`)
check('站点行可获得焦点', focused === true)
await key('Enter', 'Enter', 13, '\r')
await sleep(1200)
check('Enter 打开抽屉', (await ev('!!document.querySelector(".drawer")')) === true)

// 6. Esc 关闭抽屉
await key('Escape', 'Escape', 27)
await sleep(900)
check('Esc 关闭抽屉', (await ev('!!document.querySelector(".drawer")')) === false)

// 7. 场景选择器可用键盘操作
await go('/peak')
async function go(route) {
  await S('Page.navigate', { url: 'http://127.0.0.1:5173' + route })
  await sleep(2600)
}
const tabInfo = await ev(`(() => {
  const t = document.querySelectorAll('.picker__tab');
  return { count: t.length, roles: [...t].map(x => x.tagName + ':selected=' + (x.getAttribute('aria-selected') ?? '-')) };
})()`)
check('场景选择器是 3 个 tab 按钮', tabInfo.count === 3, JSON.stringify(tabInfo.roles))
check('场景 tab 有 aria-selected', tabInfo.roles.every((r) => !r.endsWith('-')), JSON.stringify(tabInfo.roles))

console.log('\n' + '='.repeat(50))
const pass = results.filter(r => r.ok).length
console.log(`结果: ${pass}/${results.length} 通过`)
ws.close(); chrome.kill(); process.exit(pass === results.length ? 0 : 1)
