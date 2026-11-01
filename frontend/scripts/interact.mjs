/**
 * 交互回归：模拟真实的点击路径，断言数据真的变了、图表跟着重绘、没有报错。
 * 不依赖肉眼，全部走 DOM 断言。
 */
import { spawn } from 'node:child_process'
import { mkdir, writeFile, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PORT = 9600 + Math.floor(Math.random() * 60)
const OUT = fileURLToPath(new URL('../../.probe/', import.meta.url))
await mkdir(OUT, { recursive: true })
const profile = OUT + 'ix-' + PORT
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
const errors = []
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) {
    const { res, rej } = pending.get(m.id); pending.delete(m.id)
    m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)
    return
  }
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
    errors.push(m.params.args.map((a) => a.value ?? a.description ?? '').join(' ').slice(0, 160))
  }
  if (m.method === 'Runtime.exceptionThrown') {
    errors.push('EXC ' + (m.params.exceptionDetails.exception?.description ?? m.params.exceptionDetails.text).slice(0, 200))
  }
}
const raw = (method, params = {}, sessionId) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) })) })
const { targetId } = await raw('Target.createTarget', { url: 'about:blank' })
const { sessionId } = await raw('Target.attachToTarget', { targetId, flatten: true })
const S = (m, p) => raw(m, p, sessionId)
await S('Page.enable'); await S('Runtime.enable')
await S('Emulation.setDeviceMetricsOverride', { width: 1440, height: 950, deviceScaleFactor: 1, mobile: false })

/** 点击包含指定文字的元素；找不到就让测试失败而不是崩溃 */
const clickText = async (selector, text) => {
  const ok = await ev(`(() => {
    const el = [...document.querySelectorAll(${JSON.stringify(selector)})]
      .find((n) => n.textContent.includes(${JSON.stringify(text)}));
    if (!el) return false;
    el.click();
    return true;
  })()`)
  if (!ok) throw new Error(`找不到包含「${text}」的 ${selector}`)
}

const ev = async (expr) => {
  const r = await S('Runtime.evaluate', { returnByValue: true, awaitPromise: true, expression: expr })
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? 'eval error')
  return r.result.value
}
const go = async (route) => { await S('Page.navigate', { url: 'http://127.0.0.1:5173' + route }); await sleep(2600) }

const results = []
const check = (name, ok, detail) => {
  results.push({ name, ok, detail })
  console.log((ok ? '  PASS ' : '  FAIL ') + name + (detail ? '  — ' + detail : ''))
}

// ---------- 1. 导航 ----------
await go('/overview')
const navCount = await ev('document.querySelectorAll(".nav-item").length')
check('顶栏 5 个导航项', navCount === 5, String(navCount))

for (const [label, path] of [['站点与服务', '/sites'], ['高峰与方案', '/peak'], ['异常协同', '/incidents'], ['资料与说明', '/about'], ['运营总览', '/overview']]) {
  await clickText('.nav-item', label)
  await sleep(1400)
  const url = await ev('location.pathname')
  check('导航至 ' + path, url === path, url)
}

// ---------- 2. 场景切换真的换数据 ----------
await go('/overview')
const readKpi = () => ev(`[...document.querySelectorAll('.kpi__value')].map(e => e.textContent.trim()).join('|')`)
const kpiS2 = await readKpi()
await clickText('.picker__tab', 'S1-NORMAL')
await sleep(1800)
const kpiS1 = await readKpi()
check('切换场景后 KPI 变化', kpiS1 !== kpiS2, `S2=${kpiS2} S1=${kpiS1}`)

const activeS1 = await ev(`document.querySelector('.picker__tab--on')?.textContent.trim().split('\\n')[0]`)
check('场景选中态跟随', String(activeS1).includes('S1-NORMAL'), activeS1)

// 切到 S2 再看风险
await clickText('.picker__tab', 'S2-PEAK')
await sleep(1600)
const riskTags = await ev(`[...document.querySelectorAll('.site-row .tag--danger')].length`)
check('S2 下总览出现风险标记', riskTags >= 1, String(riskTags))

// ---------- 3. 地图 → 抽屉 ----------
await go('/overview')
await ev(`document.querySelector('.site-row').click()`)
await sleep(1500)
const drawerOpen = await ev(`!!document.querySelector('.drawer')`)
check('点击站点行打开抽屉', drawerOpen === true, String(drawerOpen))
const drawerTitle = await ev(`document.querySelector('.drawer h2, .drawer__title, .drawer .panel__title')?.textContent.trim() ?? ''`)
check('抽屉有站点名', String(drawerTitle).length > 0, drawerTitle)
await ev(`document.querySelector('.drawer__close')?.click()`)
await sleep(700)
check('抽屉可关闭', (await ev(`!!document.querySelector('.drawer')`)) === false)

// 地图标记点击
await ev(`document.querySelectorAll('.site-marker')[2]?.click()`)
await sleep(1200)
check('点击地图标记打开抽屉', (await ev(`!!document.querySelector('.drawer')`)) === true)

// ---------- 4. 图表重绘 ----------
await go('/peak')
const sig = () => ev(`[...document.querySelectorAll('canvas')].map(c => {
  const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let h = 0; for (let i = 0; i < d.length; i += 4013) h = (h * 31 + d[i]) >>> 0;
  return h;
}).join('|')`)
const sigA = await sig()
await clickText('.chip', '松苑')
await sleep(1800)
const sigB = await sig()
check('切换站点后图表重绘', sigA !== sigB, sigA + ' -> ' + sigB)
const focusName = await ev(`document.querySelector('.chip--on')?.textContent.replace(/\\s+/g,' ').trim()`)
check('站点选中态跟随', String(focusName).includes('松苑'), focusName)

// ---------- 5. 工单状态流转 ----------
await go('/incidents')
const readStat = (label) => ev(`[...document.querySelectorAll('.stat')].find((s) => s.textContent.includes(${JSON.stringify(label)}))?.querySelector('.stat__n')?.textContent.trim()`)
const closedBefore = Number(await readStat('已闭环'))
await clickText('.actions__row .btn', '处理中')
await sleep(900)
const tagDoing = await ev(`document.querySelector('.detail .panel__head .tag')?.textContent.trim()`)
check('工单置为处理中', tagDoing === '处理中', tagDoing)
await clickText('.actions__row .btn', '已闭环')
await sleep(900)
check('工单置为已闭环', (await ev(`document.querySelector('.detail .panel__head .tag')?.textContent.trim()`)) === '已闭环')
const closedAfter = Number(await readStat('已闭环'))
check('统计计数同步', closedAfter === closedBefore + 1, `${closedBefore} -> ${closedAfter}`)
const ticketCount = await ev(`document.querySelectorAll('.wo').length`)
check('S2 生成多张工单', ticketCount >= 3, String(ticketCount))

// ---------- 6. 主题切换 ----------
await go('/about')
const bgDark = await ev(`getComputedStyle(document.body).backgroundColor`)
await ev(`document.querySelector('.icon-btn--theme').click()`)
await sleep(900)
const bgLight = await ev(`getComputedStyle(document.body).backgroundColor`)
check('主题切换改变底色', bgDark !== bgLight, bgDark + ' -> ' + bgLight)
check('主题持久化到 localStorage', (await ev(`localStorage.getItem('campusflow-theme')`)) !== null)

// ---------- 7. 底图切换 ----------
await go('/overview')
const layers = await ev(`[...document.querySelectorAll('.layer-btn')].map(b => b.textContent.replace(/\\s+/g,' ').trim())`)
check('两种底图可选', layers.length === 2, JSON.stringify(layers))
check('默认是手册原图', String(layers[0]).includes('手册'), String(layers[0]))
check('第二种是卫星影像', String(layers[1]).includes('卫星'), String(layers[1]))
// 手册原图默认就必须已经渲染出图片（离线可用，不依赖网络）
const imgNow = await ev(`document.querySelectorAll('.leaflet-image-layer').length`)
check('手册原图已渲染', imgNow >= 1, String(imgNow))
// 切到卫星再切回来，图片层仍要在
await ev(`document.querySelectorAll('.layer-btn')[1].click()`)
await sleep(2200)
const tiles = await ev(`document.querySelectorAll('.leaflet-tile').length`)
check('卫星影像层有瓦片', tiles > 0, String(tiles))
await ev(`document.querySelectorAll('.layer-btn')[0].click()`)
await sleep(1200)
const backToImg = await ev(`document.querySelectorAll('.leaflet-image-layer').length`)
check('切回手册原图后图片仍在', backToImg >= 1, String(backToImg))

// ---------- 8. 站点页 ----------
await go('/sites')
const cardCount = await ev(`document.querySelectorAll('.card').length`)
check('站点页 4 张卡片', cardCount === 4, String(cardCount))
await ev(`document.querySelectorAll('.card')[1].click()`)
await sleep(1200)
const detailTitle = await ev(`document.querySelector('.detail__main .panel__title')?.textContent.replace(/\\s+/g,' ').trim()`)
check('切换站点详情', String(detailTitle).includes('松苑'), detailTitle)
const rowCount = await ev(`document.querySelectorAll('.tl__scroll .tl__row').length`)
check('分时段运行表 33 行', rowCount === 33, String(rowCount))
const firstRow = await ev(`document.querySelector('.tl__scroll .tl__row')?.textContent.replace(/\\s+/g,' ').trim()`)
check('运行表首行有数据', String(firstRow).startsWith('07:00'), firstRow)

console.log('\n' + '='.repeat(50))
console.log('控制台错误:', errors.filter((e) => !e.includes('favicon')).length)
for (const e of errors.filter((x) => !x.includes('favicon')).slice(0, 8)) console.log('  ! ' + e)
const failed = results.filter((r) => !r.ok)
console.log(`结果: ${results.length - failed.length}/${results.length} 通过`)

await writeFile(OUT + 'interact.json', JSON.stringify({ results, errors }, null, 2), 'utf-8')
ws.close(); chrome.kill(); process.exit(failed.length ? 1 : 0)
