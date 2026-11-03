/**
 * 后端契约测试：直接打 Spring Boot 的接口，断言结构、数值与守恒。
 * 用法：node scripts/api.mjs [baseUrl]
 */
const BASE = process.argv[2] || 'http://127.0.0.1:8080'
const results = []
const check = (name, ok, detail) => {
  results.push(ok)
  console.log((ok ? '  PASS ' : '  FAIL ') + name + (detail ? '  — ' + detail : ''))
}
const get = async (p, init) => {
  const res = await fetch(BASE + p, init)
  const text = await res.text()
  let json = null
  try { json = JSON.parse(text) } catch { /* 非 JSON */ }
  return { status: res.status, json, text }
}

// 1. 健康检查
const h = await get('/api/health')
check('健康检查 200', h.status === 200, String(h.status))
check('返回 status=ok', h.json?.status === 'ok', JSON.stringify(h.json))

// 2. 站点
const sites = await get('/api/sites')
check('站点接口 200', sites.status === 200)
check('四个站点', Array.isArray(sites.json) && sites.json.length === 4, String(sites.json?.length))
const tao = sites.json?.find((s) => s.id === 'NH-TAOYUAN')
check('桃苑物理储位 19200', tao?.physicalSlots === 19200, String(tao?.physicalSlots))
check('桃苑 κ_i 16320', tao?.kappaI === 16320, String(tao?.kappaI))
check('桃苑通道 0.8 m', tao?.aisleM === 0.8, String(tao?.aisleM))

// 3. 场景数据
const sc = await get('/api/scenarios')
check('场景接口 200', sc.status === 200, `${(sc.text.length / 1024).toFixed(0)} KB`)
check('三个场景', sc.json?.scenarios?.length === 3, String(sc.json?.scenarios?.length))
check('33 个时间桶', sc.json?.buckets?.length === 33, String(sc.json?.buckets?.length))
const s2 = sc.json?.scenarios?.find((s) => s.scenario_id === 'S2-PEAK')
check('S2 是第 7 天', s2?.day_index === 7, String(s2?.day_index))
check('S2 桃苑占用率 83.4%', Math.abs((s2?.summary?.[0]?.occupancy_pct ?? 0) - 83.4) < 0.2, String(s2?.summary?.[0]?.occupancy_pct))
check('S2 含通道指标', typeof s2?.summary?.[0]?.aisle_ok_pct === 'number')
check('S2 含排队指标', typeof s2?.summary?.[0]?.queue_min === 'number')
check('S2 周推演 9 天', s2?.week?.length === 9, String(s2?.week?.length))

// 4. 室内布局
const lay = await get('/api/layouts/NH-TAOYUAN')
check('布局接口 200', lay.status === 200)
check('48 排货架', lay.json?.rows?.length === 48, String(lay.json?.rows?.length))
check('240 个货架号', lay.json?.params?.bays === 240, String(lay.json?.params?.bays))
check('京东 191–240 共 10 排', lay.json?.rows?.filter((r) => r.managed_by === 'JD').length === 10)
const missing = await get('/api/layouts/NH-LANYUAN')
check('兰苑无布局返回 pending', missing.json?.status === 'pending_photos', String(missing.json?.status))

// 5. 工单流转
const before = await get('/api/workorders')
const target = before.json?.[0]
check('工单接口 200', before.status === 200, String(before.json?.length) + ' 条')
const nextStatus = target?.status === 'closed' ? 'open' : 'closed'
const patched = await get(`/api/workorders/${target?.id}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status: nextStatus })
})
check('PATCH 状态成功', patched.status === 200 && patched.json?.status === nextStatus, patched.json?.status)
const after = await get('/api/workorders')
check('状态已持久化', after.json?.find((w) => w.id === target?.id)?.status === nextStatus)
const bad = await get(`/api/workorders/${target?.id}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status: 'bogus' })
})
check('非法状态被拒绝', bad.status === 400, String(bad.status))

// 6. 服务端仿真 + 守恒
const body = {
  buckets: ['08:00', '08:30', '09:00'],
  arrivals: [50, 200, 30],
  capacity: [100, 100, 100],
  pickups: [40, 60, 200],
  q0: 0,
  i0: 100,
  kappaQ: 1000,
  kappaI: 1000
}
const sim = await get('/api/simulation/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body)
})
check('仿真接口 200', sim.status === 200)
check('返回 3 行', sim.json?.rows?.length === 3, String(sim.json?.rows?.length))
const rows = sim.json?.rows ?? []
let q = body.q0
let i = body.i0
let conserved = true
rows.forEach((r, t) => {
  if (r.q + r.i !== q + i + body.arrivals[t] - r.p) conserved = false
  q = r.q
  i = r.i
})
check('守恒式成立', conserved)
check('峰值待取 150', sim.json?.peakI === 150, String(sim.json?.peakI))
check('返回通道可通行率', typeof sim.json?.aisleOkPct === 'number', String(sim.json?.aisleOkPct))

const pass = results.filter(Boolean).length
console.log('\n' + '='.repeat(50))
console.log(`结果: ${pass}/${results.length} 通过`)
process.exit(pass === results.length ? 0 : 1)
