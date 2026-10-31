# -*- coding: utf-8 -*-
"""生成 CampusFlow 演示场景数据（全部为模拟假设，非真实业务量）。

用法：
    <python> data/research/generate_demo_scenarios.py

输出：
    data/demo/scenarios.json

设计要点：
- 30 分钟时间桶，07:00—23:30 共 33 桶；桃苑 08:30—18:30 只占其中 20 桶。
- 每站处理能力 C 按"该站自身峰值桶到件量的某个比例"标定，
  使常态下基本不积压、高峰下确实出现积压，从而让风险指标可演示。
- 日取件总量略低于日到件总量（0.96），避免待取库存无限增长。
- 全部数值均为演示假设，不代表任何真实站点业务量。
"""
import json, os
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_buckets():
    t = datetime(2026, 1, 1, 7, 0)
    return [(t + timedelta(minutes=30 * i)).strftime("%H:%M") for i in range(33)]


BUCKETS = build_buckets()

# 到件权重（33 桶，07:00 起）：上午一个峰
W_ARRIVAL = [1.5, 2.5, 4.0, 6.0, 7.5, 8.0, 7.0, 6.0, 4.5, 3.0, 2.0, 2.0, 3.0,
             5.0, 6.5, 7.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.5, 1.2, 1.0,
             0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]

# 取件权重（33 桶，07:00 起）：午间、傍晚两个峰
W_PICKUP = [1.0, 2.0, 2.5, 2.0, 1.8, 1.5, 1.5, 1.8, 2.5, 4.5, 6.5, 6.0, 4.0,
            3.0, 2.8, 2.8, 3.0, 3.5, 4.0, 4.5, 6.0, 7.5, 7.0, 5.5, 4.5, 4.0,
            3.5, 3.5, 4.0, 4.0, 3.0, 2.0, 1.0]

SITES = [
    {"id": "NH-TAOYUAN",  "name": "桃苑物流服务中心", "open": "08:30", "close": "18:30",
     "lo": 3, "hi": 22, "share_a": 0.34, "share_d": 0.30, "cap_factor": 0.78},
    {"id": "NH-SONGYUAN", "name": "松苑无人菜鸟驿站", "open": "07:00", "close": "23:30",
     "lo": 0, "hi": 32, "share_a": 0.26, "share_d": 0.27, "cap_factor": 0.78},
    {"id": "NH-MEIYUAN",  "name": "梅苑无人菜鸟驿站", "open": "07:00", "close": "23:30",
     "lo": 0, "hi": 32, "share_a": 0.22, "share_d": 0.24, "cap_factor": 0.78},
    {"id": "NH-LANYUAN",  "name": "兰苑无人菜鸟驿站", "open": "07:00", "close": "23:30",
     "lo": 0, "hi": 32, "share_a": 0.18, "share_d": 0.19, "cap_factor": 0.78},
]


def round_preserve(total, weights):
    """最大余数法：把 total 按 weights 拆成整数，且**和恰好等于 round(total)**。

    逐项 round 会累积误差（33 桶下来能差十几件），
    而"分流前后总量守恒""S3 与 S2 到件总量完全相同"这类叙事必须逐件对得上。
    """
    target = int(round(total))
    w_sum = sum(weights)
    if w_sum <= 0:
        return [0] * len(weights)
    raw = [target * w / w_sum for w in weights]
    base = [int(x) for x in raw]
    rest = target - sum(base)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in order[:rest]:
        base[i] += 1
    assert sum(base) == target
    return base


def calibrate_norm(site, a_day, d_day):
    """用常态日量标定站点的"物理常量"：处理能力 C0、积压上限 κ_q、待取上限 κ_i、初始待取 i0。

    这些是设备与场地参数，**不随场景变化**——场景只改变到件量，以及运营措施
    （加开处理位 = 乘 C 的倍数、临时扩充待取区 = 乘 κ_i 的倍数）。
    早先的实现让 C 随当场景到件量浮动，等于"高峰自动扩容"，与"库容物理不变"的
    叙事自相矛盾，故改为在此处一次标定。
    """
    lo, hi = site["lo"], site["hi"]
    w_a = sum(W_ARRIVAL[lo:hi + 1])
    peak_a_bucket = a_day * max(W_ARRIVAL[lo:hi + 1]) / w_a
    C0 = max(1, int(round(peak_a_bucket * site["cap_factor"])))
    return {"C0": C0, "KQ0": int(round(C0 * 1.60)), "KI0": int(round(d_day * 0.85)),
            "I0": int(round(d_day * 0.10))}


def build_site(site, a_day, d_day, const, cap_mult=1.0, kappa_q_mult=1.0, kappa_i_mult=1.0):
    """a_day / d_day 已含分流，直接使用，保证分流前后总量守恒。"""
    lo, hi = site["lo"], site["hi"]
    w_a = sum(W_ARRIVAL[lo:hi + 1])
    w_d = sum(W_PICKUP)

    C = max(1, int(round(const["C0"] * cap_mult)))
    k_q = int(round(const["KQ0"] * kappa_q_mult))
    k_i = int(round(const["KI0"] * kappa_i_mult))
    i0 = const["I0"]

    # 营业时段外的到件权重置 0，再整体按最大余数法拆分，保证日到件量与 a_day 一致
    a_w = [W_ARRIVAL[i] if lo <= i <= hi else 0.0 for i in range(len(BUCKETS))]
    arrivals = round_preserve(a_day, a_w)
    pickups = round_preserve(d_day, W_PICKUP)
    demand = [
        {"bucket": b, "arrivals": arrivals[i], "capacity": C, "pickups": pickups[i]}
        for i, b in enumerate(BUCKETS)
    ]

    peak_A = max(r["arrivals"] for r in demand)

    return {
        "site_id": site["id"],
        "site_name": site["name"],
        "service_hours": {"open": site["open"], "close": site["close"], "bucket_count": hi - lo + 1},
        "params": {
            "capacity_per_bucket": C,
            "kappa_q": k_q,
            "kappa_i": k_i,
            "q0": 0,
            "i0": i0,
            # 站点物理常量（不随场景变化），前端用于"上限说明"与后端复算
            "capacity_norm": const["C0"],
            "kappa_q_norm": const["KQ0"],
            "kappa_i_norm": const["KI0"],
        },
        "daily_totals": {"arrivals": sum(r["arrivals"] for r in demand),
                         "pickups": sum(r["pickups"] for r in demand),
                         "peak_bucket_arrivals": peak_A},
        "demand": demand,
    }


def simulate(site):
    p = site["params"]
    Q, I = p["q0"], p["i0"]
    rows = []
    for r in site["demand"]:
        A, C, D = r["arrivals"], r["capacity"], r["pickups"]
        S = min(Q + A, C)
        Q2 = Q + A - S
        P = min(D, I + S)
        I2 = I + S - P
        assert Q2 + I2 == Q + I + A - P, "守恒式被破坏 %s %s" % (site["site_id"], r["bucket"])
        rows.append({"bucket": r["bucket"],
                     "q": Q2, "i": I2, "s": S, "p": P, "unmet": D - P,
                     "risk_q": Q2 > p["kappa_q"], "risk_i": I2 > p["kappa_i"]})
        Q, I = Q2, I2
    return rows


# 场景只改三样东西：
#   cap_mult        人手带来的处理能力倍数（相对常态常量 C0）
#   kappa_q_mult    未处理积压场的临时扩容倍数
#   kappa_i_mult    待取区的临时扩容倍数
# 站点常量 C0 / κ_q0 / κ_i0 / i0 一律按常态日标定一次，三场景共用。
DESIGN_SCENARIO = "S2-PEAK"

SCENARIOS = [
    {"scenario_id": "S1-NORMAL", "name": "常态工作日", "classification": "SIMULATED",
     "note": "演示基线。站点仍按双十一设计峰值建成，设备与货架不缩水，因此常态下能力有富余、不出现风险",
     "total_a": 6200, "total_d": 5952,
     "cap_mult": 1.00, "kappa_q_mult": 1.00, "kappa_i_mult": 1.00},
    {"scenario_id": "S2-PEAK", "name": "双十一高峰", "classification": "SIMULATED",
     "note": "到件量按常态 2.2 倍假设（13,640 件），当日取件需求 9,300 件（约 68%），差额结转为次日待取；处理能力 C 与库容阈值 κ_q / κ_i 都是站点建成时的固定值，高峰期间不扩容，因此桃苑待取区先被撑满",
     "total_a": 13640, "total_d": 9300,
     "cap_mult": 1.00, "kappa_q_mult": 1.00, "kappa_i_mult": 1.00},
    {"scenario_id": "S3-PEAK-ADJ", "name": "高峰 + 分流与增能", "classification": "SIMULATED",
     "note": "到件总量与取件需求都与 S2 完全相同，同时改三件事：①桃苑把 18% 到件转给三个无人站（松苑 7%、梅苑 6%、兰苑 5%）；②各站加开临时处理位（C×1.35）；③各站临时扩充待取区（κ_i×1.5）与积压周转区（κ_q×1.2）",
     "total_a": 13640, "total_d": 9300,
     "transfers": {"NH-TAOYUAN": {"NH-SONGYUAN": 0.07, "NH-MEIYUAN": 0.06, "NH-LANYUAN": 0.05}},
     "cap_mult": 1.35, "kappa_q_mult": 1.20, "kappa_i_mult": 1.50},
]


def main():
    out = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "warning": "本文件全部为模拟数据，不代表任何真实站点业务量；严禁当作公开统计引用",
        "classification": "SIMULATED",
        "model": {
            "bucket_minutes": 30,
            "formulas": {
                "S": "min(Q + A, C)",
                "Q_next": "Q + A - S",
                "P": "min(D, I + S)  取件关闭时 P = 0",
                "I_next": "I + S - P",
                "conservation": "Q_next + I_next = Q + I + A - P",
                "risk": "Q_next > kappa_q 或 I_next > kappa_i",
            },
        },
        "buckets": BUCKETS,
        "scenarios": [],
    }

    # 站点物理常量：按"设计峰值场景"（双十一）标定一次，之后所有场景共用。
    # 现实里站点的处理位数量、货架面积就是按最高峰设计的，建成后不会随当天件量伸缩，
    # 所以常量必须只标定一次，而不是每个场景各算各的。
    norm = next(s for s in SCENARIOS if s["scenario_id"] == DESIGN_SCENARIO)
    consts = {}
    for site in SITES:
        consts[site["id"]] = calibrate_norm(
            site, norm["total_a"] * site["share_a"], norm["total_d"] * site["share_d"])

    print("站点常量（按 %s 标定）:" % DESIGN_SCENARIO)
    for k, c in consts.items():
        print("   %-13s C0=%-4d KQ0=%-4d KI0=%-5d I0=%d" % (k, c["C0"], c["KQ0"], c["KI0"], c["I0"]))

    for sc in SCENARIOS:
        # 先算不考虑分流的基础日量
        base_a = {s["id"]: sc["total_a"] * s["share_a"] for s in SITES}
        base_d = {s["id"]: sc["total_d"] * s["share_d"] for s in SITES}

        # 分流：transfers[源站] = {目标站: 源站到件量的比例}
        a_day = dict(base_a)
        for src, targets in (sc.get("transfers") or {}).items():
            for dst, frac in targets.items():
                moved = base_a[src] * frac
                a_day[src] -= moved
                a_day[dst] += moved

        # 守恒自检
        assert abs(sum(a_day.values()) - sum(base_a.values())) < 1e-6, "分流破坏了到件总量守恒"

        sites = []
        for site in SITES:
            cm = (sc.get("cap_mult_by_site") or {}).get(site["id"], sc.get("cap_mult", 1.0))
            kqm = (sc.get("kappa_q_mult_by_site") or {}).get(site["id"], sc.get("kappa_q_mult", 1.0))
            kim = (sc.get("kappa_i_mult_by_site") or {}).get(site["id"], sc.get("kappa_i_mult", 1.0))
            sites.append(build_site(site, a_day[site["id"]], base_d[site["id"]],
                                    consts[site["id"]], cm, kqm, kim))

        sims = [simulate(s) for s in sites]

        # 分流守恒：S3 各站到件总量必须与 S2 相等
        summary = []
        for s, rows in zip(sites, sims):
            summary.append({
                "site_id": s["site_id"],
                "daily_arrivals": s["daily_totals"]["arrivals"],
                "daily_pickups": s["daily_totals"]["pickups"],
                "peak_q": max(r["q"] for r in rows),
                "peak_i": max(r["i"] for r in rows),
                "risk_buckets": sum(1 for r in rows if r["risk_q"] or r["risk_i"]),
                "risk_q_buckets": sum(1 for r in rows if r["risk_q"]),
                "risk_i_buckets": sum(1 for r in rows if r["risk_i"]),
                "total_pickup": sum(r["p"] for r in rows),
                "unmet": sum(r["unmet"] for r in rows),
                "first_risk_bucket": next((r["bucket"] for r in rows if r["risk_q"] or r["risk_i"]), None),
            })

        out["scenarios"].append({
            "scenario_id": sc["scenario_id"],
            "name": sc["name"],
            "classification": sc["classification"],
            "note": sc["note"],
            "total_daily_arrivals": sum(x["daily_arrivals"] for x in summary),
            "total_daily_pickups": sum(x["daily_pickups"] for x in summary),
            "sites": sites,
            "summary": summary,
            "timeline": [{"bucket": rows[0]["bucket"], "sites": rows} for rows in zip(*sims)],
        })

    path = os.path.join(BASE, "demo", "scenarios.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("wrote", path, os.path.getsize(path), "bytes")
    for sc in out["scenarios"]:
        print("\n==", sc["scenario_id"], sc["name"],
              " total_arr=%d total_pick=%d" % (sc["total_daily_arrivals"], sc["total_daily_pickups"]))
        for s in sc["summary"]:
            print("   %-13s arr=%-5d pick=%-5d peakQ=%-4d peakI=%-5d risk=%-3d first=%s"
                  % (s["site_id"], s["daily_arrivals"], s["daily_pickups"],
                     s["peak_q"], s["peak_i"], s["risk_buckets"], s["first_risk_bucket"]))


if __name__ == "__main__":
    main()
