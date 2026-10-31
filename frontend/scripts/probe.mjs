/**
 * 用 Chrome DevTools Protocol 检查页面：
 *  - 收集 console 错误与未捕获异常
 *  - 检查横向溢出（在指定视口下 scrollWidth > clientWidth）
 *  - 截图存到 .probe/
 * 用法: node scripts/probe.mjs [baseUrl]
 */
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { mkdir, writeFile, rm } from 'node:fs/promises'
import { setTimeout as sleep } from 'node:timers/promises'

const BASE = process.argv[2] || 'http://127.0.0.1:5173'
const ROUTES = ['/overview', '/sites', '/peak', '/incidents', '/about']
const WIDTHS = [1280, 1440, 1920]
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9333
const OUT = fileURLToPath(new URL('../../.probe/', import.meta.url))

await mkdir(OUT, { recursive: true })

const profile = OUT + 'profile'
await rm(profile, { recursive: true, force: true })

const chrome = spawn(CHROME, [
  '--headless=new',
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${profile}`,
  '--no-first-run',
  '--no-default-browser-check',
  '--disable-gpu',
  '--hide-scrollbars',
  '--force-device-scale-factor=1',
  'about:blank'
], { stdio: 'ignore' })

async function getWs() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`)
      const j = await r.json()
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl
    } catch { /* not up yet */ }
    await sleep(250)
  }
  throw new Error('chrome devtools not reachable')
}

const wsUrl = await getWs()
const ws = new WebSocket(wsUrl)
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })

let msgId = 0
const pending = new Map()
const events = []
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) {
    const { res, rej } = pending.get(m.id)
    pending.delete(m.id)
    m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)
  } else if (m.method) {
    events.push(m)
  }
}

function send(method, params = {}, sessionId) {
  const id = ++msgId
  return new Promise((res, rej) => {
    pending.set(id, { res, rej })
    ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }))
  })
}

// 新建一个 page target 并 attach
const { targetId } = await send('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true })

const S = (m, p) => send(m, p, sessionId)

await S('Page.enable')
await S('Runtime.enable')
await S('Log.enable')

const consoleErrors = []
const exceptions = []
ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data)
  if (m.sessionId !== sessionId) return
  if (m.method === 'Runtime.consoleAPICalled' && (m.params.type === 'error' || m.params.type === 'warning')) {
    consoleErrors.push({
      type: m.params.type,
      text: m.params.args.map((a) => a.value ?? a.description ?? a.type).join(' ')
    })
  }
  if (m.method === 'Runtime.exceptionThrown') {
    exceptions.push(m.params.exceptionDetails.exception?.description ?? m.params.exceptionDetails.text)
  }
  if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') {
    consoleErrors.push({ type: 'log', text: m.params.entry.text + ' ' + (m.params.entry.url ?? '') })
  }
})

const results = []

for (const width of WIDTHS) {
  await S('Emulation.setDeviceMetricsOverride', {
    width, height: 900, deviceScaleFactor: 1, mobile: false
  })

  for (const route of ROUTES) {
    consoleErrors.length = 0
    exceptions.length = 0

    await S('Page.navigate', { url: BASE + route })
    await sleep(2600)

    let probe = null
    try {
      const r = await S('Runtime.evaluate', {
        returnByValue: true,
        expression: `(() => {
          const de = document.documentElement;
          const overflowX = de.scrollWidth - de.clientWidth;
          const offenders = [];
          document.querySelectorAll('body *').forEach((el) => {
            const rc = el.getBoundingClientRect();
            if (rc.width === 0) return;
            if (rc.right > de.clientWidth + 1.5 || rc.left < -1.5) {
              const cs = getComputedStyle(el);
              if (cs.position === 'fixed') return;
              offenders.push({
                tag: el.tagName.toLowerCase(),
                cls: (el.className && String(el.className).slice(0, 60)) || '',
                left: Math.round(rc.left), right: Math.round(rc.right)
              });
            }
          });
          const canvases = [...document.querySelectorAll('canvas')].map((c) => ({ w: c.width, h: c.height }));
          return {
            title: document.title,
            h1: document.querySelector('h1')?.textContent?.trim() ?? null,
            overflowX,
            offenders: offenders.slice(0, 6),
            offenderCount: offenders.length,
            canvases,
            mapReady: !!document.querySelector('.leaflet-container'),
            markers: document.querySelectorAll('.site-marker').length,
            panelCount: document.querySelectorAll('.panel, .kpi, .card').length,
            bodyText: document.body.innerText.length
          };
        })()`
      })
      probe = r.result.value
    } catch (e) {
      probe = { error: String(e) }
    }

    const shot = await S('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
    const file = `${OUT}${route.replace(/\//g, '')}-${width}.png`
    await writeFile(file, Buffer.from(shot.data, 'base64'))

    results.push({ width, route, probe, errors: [...consoleErrors], exceptions: [...exceptions] })
  }
}

await writeFile(OUT + 'report.json', JSON.stringify(results, null, 2), 'utf-8')

// 精简控制台输出
for (const r of results) {
  const p = r.probe || {}
  const errs = r.errors.filter((e) => e.type !== 'warning')
  console.log(
    `${r.width} ${r.route.padEnd(11)} overflow=${p.overflowX ?? '?'} offenders=${p.offenderCount ?? '?'} ` +
    `panels=${p.panelCount ?? '?'} map=${p.mapReady} markers=${p.markers ?? '?'} ` +
    `canvas=${p.canvases?.length ?? 0} err=${errs.length} exc=${r.exceptions.length}`
  )
  for (const e of errs.slice(0, 4)) console.log('    ERR ' + e.text.slice(0, 180))
  for (const e of r.exceptions.slice(0, 3)) console.log('    EXC ' + String(e).slice(0, 200))
  for (const o of (p.offenders ?? []).slice(0, 4)) console.log('    OF  ' + o.tag + '.' + o.cls + ' ' + o.left + '~' + o.right)
}

ws.close()
chrome.kill()
process.exit(0)
