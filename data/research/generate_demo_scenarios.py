# -*- coding: utf-8 -*-
"""生成三场景数据（v2：第 7 天视角 + 物理容量口径 + 周累积）

关键改动（2026-11-03）：
  1. κ_i 不再反推，改为 物理储位 × 85%（桃苑物理储位由实景照片推算 19,200）
  2. i0 不再是从空仓起步的 279，改为"双十一第 7 天早上"的累积存量
  3. 新增周视角：7 天逐日存量 + 第 8/9 天外推
  4. 新增两个风险指标：通道可通行率、高峰排队时长
"""
import json
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'data', 'demo', 'scenarios.json')

BUCKETS = []
for h in range(7, 24):
    BUCKETS.append('%02d:00' % h)
    BUCKETS.append('%02d:30' % h)
BUCKETS.append('23:30')
BUCKETS = BUCKETS[:33]

# 到件权重（33 桶）：早班进城、午间补车、傍晚二次补车
W_ARRIVAL = [0.01, 0.02, 0.04, 0.07, 0.09, 0.08, 0.06, 0.05, 0.05, 0.04, 0.03,
             0.04, 0.07, 0.08, 0.07, 0.05, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01,
             0.01, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
# 取件权重：午间与晚饭后两个峰
W_PICKUP = [0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
            0.06, 0.06, 0.05, 0.05, 0.05, 0.04, 0.05, 0.06, 0.06, 0.05, 0.04,
            0.03, 0.02, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]


def norm(w):
    s = sum(w)
    return [x / s for x in w]


W_ARRIVAL = norm(W_ARRIVAL)
W_PICKUP = norm(W_PICKUP)

SITES = [
    {"id": "NH-TAOYUAN", "name": "桃苑物流服务中心", "open": "08:30", "close": "18:30",
     "lo": 3, "hi": 23, "cap_factor": 1.00, "physical_slots": 24000,
     "physical_source": "observed", "aisle_m": 0.8, "counters": 2},
    {"id": "NH-SONGYUAN", "name": "松苑无人菜鸟驿站", "open": "07:00", "close": "23:30",
     "lo": 0, "hi": 32, "cap_factor": 1.10, "physical_slots": 7900,
     "physical_source": "assumed", "aisle_m": 0.8, "counters": 1},
    {"id": "NH-MEIYUAN", "name": "梅苑无人菜鸟驿站", "open": "07:00", "close": "23:30",
     "lo": 0, "hi": 32, "cap_factor": 1.10, "physical_slots": 6700,
     "physical_source": "assumed", "aisle_m": 0.8, "counters": 1},
    {"id": "NH-LANYUAN", "name": "兰苑无人菜鸟驿站", "open": "07:00", "close": "23:30",
     "lo": 0, "hi": 32, "cap_factor": 1.10, "physical_slots": 5500,
     "physical_source": "observed", "aisle_m": 0.8, "counters": 1},
]

SITE_SHARE = {"NH-TAOYUAN": 0.34, "NH-SONGYUAN": 0.26, "NH-MEIYUAN": 0.22, "NH-LANYUAN": 0.18}
PICKUP_RATIO = 0.68
# 第 7 天各站"设计占用率"：场景编排参数（不是实测），用来把当天的存量定在预定水位
DAY7_TARGET = {"NH-TAOYUAN": 0.82, "NH-SONGYUAN": 0.88, "NH-MEIYUAN": 0.86, "NH-LANYUAN": 0.84}
AVG_STAY_DAYS = 1.5
KAPPA_I_SHARE = 0.85      # 运营上限 = 物理储位 × 85%
WARN_SHARE = 0.70
CHANNEL_AREA = {"NH-TAOYUAN": 144.0, "NH-SONGYUAN": 60.0, "NH-MEIYUAN": 60.0, "NH-LANYUAN": 60.0}
PILE_RATIO = 0.008        # 落地临时堆放的件数占在架件数的比例
SERVICE_SEC = 25          # 自助扫码 25 秒/件
PEAK_HOUR_SHARE = 0.18    # 晚高峰占日取件量


def round_preserve(total, weights):
    raw = [total * w for w in weights]
    base = [int(math.floor(x)) for x in raw]
    rest = total - sum(base)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in range(rest):
        base[order[i % len(order)]] += 1
    return base


def build(site, a_day, d_day):
    lo, hi = site['lo'], site['hi']
    a_w = [W_ARRIVAL[i] if lo <= i <= hi else 0.0 for i in range(len(BUCKETS))]
    arrivals = round_preserve(a_day, a_w)
    pickups = round_preserve(d_day, W_PICKUP)

    w_a = sum(a_w)
    peak_bucket = max(arrivals)
    C = max(1, int(round(peak_bucket * site['cap_factor'])))
    k_q = int(round(C * 1.6))
    phys = site['physical_slots']
    k_i = int(round(phys * KAPPA_I_SHARE))
    warn_i = int(round(phys * WARN_SHARE))

    net = a_day - d_day
    steady = max(0, int(round(net * AVG_STAY_DAYS)))

    return {
        "site_id": site['id'],
        "site_name": site['name'],
        "service_hours": {"open": site['open'], "close": site['close'], "bucket_count": hi - lo + 1},
        "params": {
            "capacity_per_bucket": C, "kappa_q": k_q, "kappa_i": k_i, "q0": 0, "i0": steady,
            "capacity_norm": C, "kappa_q_norm": k_q, "kappa_i_norm": k_i,
            "physical_slots": phys, "physical_source": site['physical_source'],
            "kappa_i_warn": warn_i, "aisle_m": site['aisle_m'], "counters": site['counters'],
        },
        "daily_totals": {"arrivals": a_day, "pickups": d_day, "peak_bucket_arrivals": peak_bucket},
        "demand": [{"bucket": b, "arrivals": arrivals[i], "capacity": C, "pickups": pickups[i]}
                   for i, b in enumerate(BUCKETS)],
        "net_per_day": net,
        "steady_i": steady,
    }


def simulate(site, i0, k_i, k_q):
    Q, I = site['params']['q0'], i0
    rows = []
    for r in site['demand']:
        A, C, D = r['arrivals'], r['capacity'], r['pickups']
        S = min(Q + A, C)
        Q2 = Q + A - S
        P = min(D, I + S)
        I2 = I + S - P
        assert Q2 + I2 == Q + I + A - P, '守恒式被破坏 %s %s' % (site['site_id'], r['bucket'])
        rows.append({"bucket": r['bucket'], "q": Q2, "i": I2, "s": S, "p": P,
                     "unmet": D - P, "risk_q": Q2 > k_q, "risk_i": I2 > k_i})
        Q, I = Q2, I2
    return rows


def metrics(site, phys, peak_i, d_day, counters):
    """通道可通行率与高峰排队时长"""
    occ = peak_i / phys if phys else 0
    # 临时堆放：约 0.8% 的在架件会落地（大件、待退件、当日未上架），每件占 0.25 m²
    pile = peak_i * PILE_RATIO * 0.25
    aisle_ok = max(0.0, min(1.0, 1 - pile / CHANNEL_AREA[site]))
    peak_hour = d_day * PEAK_HOUR_SHARE
    per_min = 60.0 / SERVICE_SEC
    cap_hour = 60 * per_min * counters
    backlog = max(0.0, peak_hour - cap_hour)
    queue_min = round(backlog / (per_min * counters), 1)
    return occ, aisle_ok, queue_min


SCENARIOS = [
    {"scenario_id": "S1-NORMAL", "name": "常态工作日", "total_a": 7750, "total_d": 7440,
     "note": "双十一前的常态基线。站点按峰值建成，设备与货架不缩水，因此常态下能力有富余。"},
    {"scenario_id": "S2-PEAK", "name": "双十一第 7 天", "total_a": 17050, "total_d": 11625,
     "note": "连续第 7 天高峰。货架已用到八成，通道开始被临时堆放挤占；再不管，第 9 天满仓。"},
    {"scenario_id": "S3-PEAK-ADJ", "name": "第 7 天 + 分流与增能", "total_a": 17050, "total_d": 11625,
     "note": "同样第 7 天的量，但桃苑把 18% 到件转给三个无人站、加开第 3 台自助机、扩待取区。"},
]


def main():
    scen_out = []
    for idx, sc in enumerate(SCENARIOS):
        day_index = 7 if sc['scenario_id'] != 'S1-NORMAL' else 1
        sites = []
        shares = dict(SITE_SHARE)
        if sc['scenario_id'] == 'S3-PEAK-ADJ':
            # 桃苑转出 18%，按 7/6/5 分给三辅站
            moved = SITE_SHARE['NH-TAOYUAN'] * 0.18
            shares['NH-TAOYUAN'] -= moved
            shares['NH-SONGYUAN'] += moved * 7 / 18
            shares['NH-MEIYUAN'] += moved * 6 / 18
            shares['NH-LANYUAN'] += moved * 5 / 18

        arr_alloc = round_preserve(sc['total_a'], [shares[s['id']] for s in SITES])
        pick_alloc = round_preserve(sc['total_d'], [SITE_SHARE[s['id']] for s in SITES])

        adjust = sc['scenario_id'] == 'S3-PEAK-ADJ'
        for i, site in enumerate(SITES):
            built = build(site, arr_alloc[i], pick_alloc[i])
            net = built['net_per_day']
            if day_index == 1:
                i0 = built['steady_i']
            else:
                # 让"第 day_index 天收盘"落在设计占用率上，再倒推当天早上的存量
                target = DAY7_TARGET[site['id']] * site['physical_slots']
                i0 = target - net * 1.0 - (day_index - 7) * net
            built['params']['i0'] = int(round(i0))
            if adjust:
                built['params']['counters'] = built['params']['counters'] + (1 if site['id'] == 'NH-TAOYUAN' else 1)
            built['day_index'] = day_index
            sites.append(built)

        timeline = []
        for bi, b in enumerate(BUCKETS):
            timeline.append({"bucket": b, "sites": []})
        for site in sites:
            rows = simulate(site, site['params']['i0'], site['params']['kappa_i'], site['params']['kappa_q'])
            site['rows'] = rows
            for bi, r in enumerate(rows):
                timeline[bi]['sites'].append({"bucket": r['bucket'], "q": r['q'], "i": r['i'],
                                              "s": r['s'], "p": r['p'], "unmet": r['unmet'],
                                              "risk_q": r['risk_q'], "risk_i": r['risk_i']})

        summary = []
        for site in sites:
            rows = site['rows']
            phys = site['params']['physical_slots']
            peak_i = max(r['i'] for r in rows)
            peak_q = max(r['q'] for r in rows)
            occ, aisle_ok, queue = metrics(site['site_id'], phys, peak_i, site['daily_totals']['pickups'],
                                           site['params']['counters'])
            if occ >= 1.0:
                level = 'overflow'
            elif occ >= KAPPA_I_SHARE:
                level = 'limit'
            elif occ >= WARN_SHARE:
                level = 'watch'
            else:
                level = 'normal'
            summary.append({
                "site_id": site['site_id'],
                "daily_arrivals": site['daily_totals']['arrivals'],
                "daily_pickups": site['daily_totals']['pickups'],
                "peak_q": peak_q, "peak_i": peak_i,
                "risk_buckets": sum(1 for r in rows if r['risk_q'] or r['risk_i']),
                "risk_q_buckets": sum(1 for r in rows if r['risk_q']),
                "risk_i_buckets": sum(1 for r in rows if r['risk_i']),
                "total_pickup": sum(r['p'] for r in rows),
                "unmet": sum(r['unmet'] for r in rows),
                "first_risk_bucket": next((r['bucket'] for r in rows if r['risk_q'] or r['risk_i']), None),
                "physical_slots": phys,
                "occupancy_pct": round(occ * 100, 1),
                "level": level,
                "aisle_ok_pct": round(aisle_ok * 100, 1),
                "queue_min": queue,
                "i0": site['params']['i0'],
                "net_per_day": site['net_per_day'],
            })

        # 周累积（含第 8、9 天外推）
        week = []
        for d in range(1, 10):
            day_sites = []
            for site, sumr in zip(sites, summary):
                phys = site['params']['physical_slots']
                target_end = DAY7_TARGET[site['site_id']] * phys
                if d <= 7:
                    # 第 1 天从稳态起步，第 7 天收盘落在设计占用率上，中间线性
                    end = site['steady_i'] + (target_end - site['steady_i']) * d / 7.0
                else:
                    end = target_end + (d - 7) * site['net_per_day']
                start = end - site['net_per_day']
                occ = end / site['params']['physical_slots']
                day_sites.append({
                    "site_id": site['site_id'],
                    "start_i": int(round(start)), "end_i": int(round(end)),
                    "occupancy_pct": round(occ * 100, 1),
                    "level": ('overflow' if occ >= 1.0 else 'limit' if occ >= KAPPA_I_SHARE
                              else 'watch' if occ >= WARN_SHARE else 'normal'),
                    "projected": d > 7,
                })
            week.append({"day": d, "sites": day_sites})

        scen_out.append({
            "scenario_id": sc['scenario_id'], "name": sc['name'], "classification": "SIMULATED",
            "note": sc['note'],
            "day_index": day_index,
            "total_daily_arrivals": sum(s['daily_totals']['arrivals'] for s in sites),
            "total_daily_pickups": sum(s['daily_totals']['pickups'] for s in sites),
            "sites": sites,
            "summary": summary,
            "timeline": timeline,
            "week": week,
        })

    bundle = {
        "schema_version": "2.0",
        "generated_at": "2026-11-03",
        "warning": "本文件全部为模拟数据，不代表任何真实站点业务量；严禁当作公开统计引用。",
        "classification": "SIMULATED",
        "model": {
            "bucket_minutes": 30,
            "formulas": {
                "S_t": "min(Q_t + A_t, C_t) 本时段实际处理量",
                "Q_(t+1)": "Q_t + A_t - S_t 未处理积压结转",
                "P_t": "min(D_t, I_t + S_t) 实际取走量",
                "I_(t+1)": "I_t + S_t - P_t 待取库存结转",
                "守恒校验": "Q_(t+1) + I_(t+1) = Q_t + I_t + A_t - P_t",
            },
            "kappa_i_rule": "κ_i = 物理储位 × 85%（桃苑物理储位 19,200 来自实景照片 240 架 × 4 层 × 20 位）",
            "i0_rule": "i0 = 稳态存量 + (周内第 n 天 - 1) × 日净增；稳态存量 = 日净增 × 平均滞留 1.5 天",
        },
        "buckets": BUCKETS,
        "scenarios": scen_out,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(bundle, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('written', OUT, os.path.getsize(OUT), 'bytes')
    for sc in scen_out:
        print('%s day=%d  ' % (sc['scenario_id'], sc['day_index']), end='')
        for s in sc['summary']:
            print('%s occ=%.1f%% lv=%-8s ais=%.0f%% q=%.0fmin  ' % (
                s['site_id'][3:5], s['occupancy_pct'], s['level'], s['aisle_ok_pct'], s['queue_min']), end='')
        print()


main()
