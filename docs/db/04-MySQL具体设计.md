# CampusFlow / 驿链 · MySQL 具体设计（v2）

> 版本：v2.0 · 2026-11-04 · 与《03-MySQL接入实施规划》配套
> 本文写"具体怎么实现"：实体映射、仓储查询、五个新功能的接口契约、前端改动点。

---

## 一、为什么要有 MySQL：五个新功能

H2 只用来"能跑起来"，MySQL 才让下面五件事成立：

| # | 新功能 | 用到的表 | 用户能看到什么 |
|---|---|---|---|
| F1 | **仿真运行历史** | simulation_run + sim_result | 每跑一次存一次，能看到历次峰值与风险桶，可对比 |
| F2 | **工单流转审计** | work_order + workorder_event | 工单详情里的处理记录变成真实事件流（谁、何时、从什么状态到什么状态） |
| F3 | **取件码查位置** | pickup_code + parcel + slot + shelf | 输入 108-3-2441，直接告诉你"3 号架 2 层 第 12 位，韵达" |
| F4 | **参数版本** | param_version | 页面显示"参数 v1.0 · 9 实测 / 1 公开 / 17 假设"，点开能看快照 |
| F5 | **承运商在架统计** | parcel + carrier | 每站在架件按承运商分组，柱状图 |

> 这五个都**不是**原来用 JSON 能做的：F1 需要写入、F2 需要流水、F3 需要三表连接、
> F4 需要版本快照、F5 需要 GROUP BY。

---

## 二、实体映射要点

全部实体放 `edu.cumt.campusflow.model`，统一约定：

- 主键：业务码用 `String + `Id`；流水表用 `Long + `GeneratedValue(IDENTITY)`
- 命名：Java 驼峰 ↔ 数据库 snake_case 由 Hibernate 默认策略处理，必要时显式 `Column(name=...)`
- 时间：`LocalDateTime` ↔ `DATETIME(3)`
- 关联：**默认 LAZY**，页面上要的字段用 `EntityGraph` 或投影接口取，避免 N+1

关键映射（节选）：

```java
`Entity `Table(name = "slot")
public class Slot {
    `Id private String id;                       // S-191-3-12
    `ManyToOne(fetch = LAZY) `JoinColumn(name = "shelf_id")
    private Shelf shelf;
    private int tier;                            // 1-4
    `Column(name = "cell_no") private int cellNo; // 1-20
    `OneToOne(fetch = LAZY) `JoinColumn(name = "parcel_id", unique = true)
    private Parcel parcel;                       // null = 空位
}
```

```java
`Entity `Table(name = "pickup_code")
`IdClass(PickupCodeId.class)
public class PickupCode {
    `Id `Column(name = "site_id") private String siteId;
    `Id private String code;                     // 108-3-2441
    `OneToOne(fetch = LAZY) `JoinColumn(name = "parcel_id", unique = true)
    private Parcel parcel;
    private LocalDateTime issuedAt;
}
```

---

## 三、五个新功能的接口契约

### F1 仿真运行历史

```
POST /api/simulations
  body: { scenarioId: "S2-PEAK", seed: 42, note: "答辩演示" }
  200 : { runId: 7, scenarioId: "S2-PEAK", createdAt: "2026-11-04T10:20:31",
          peakI: 16016, riskBuckets: 32, buckets: 33 }

GET /api/simulations?scenarioId=S2-PEAK&limit=10
  200 : [ { runId, scenarioId, createdAt, peakI, riskBuckets, paramVersion } ]

GET /api/simulations/{runId}
  200 : { run: {...}, rows: [ { siteId, bucket, q, i, s, p, unmet, riskQ, riskI } ] }
```

落库逻辑：一次 POST 在**同一事务**里写 1 条 `simulation_run` + 132 条 `sim_result`（4 站 × 33 桶），
写完回读校验 `peak_i` 与逐桶最大值一致。

### F2 工单流转审计

```
PATCH /api/workorders/{id}   body: { status: "doing", actor: "调度员", note: "已增派人手" }
  200 : { id, status: "doing", updatedAt, events: [ { from: "open", to: "doing", actor, atTime } ] }

GET /api/workorders/{id}/events
  200 : [ { id, fromStatus, toStatus, actor, atTime, note } ]   // 按 at_time 升序
```

约束：`status` 只允许 open/doing/closed；非法值返回 400；同一状态重复提交不写事件（幂等）。

### F3 取件码查位置

```
GET /api/pickup/{code}?siteId=NH-TAOYUAN
  200 : { code: "108-3-2441", siteId: "NH-TAOYUAN", siteName: "桃苑物流服务中心",
          shelfNo: 108, zoneId: "Z-C3", tier: 3, cell: 12,
          carrier: "韵达", parcelId: "P012345", shelvedAt: "2026-11-04T09:12:00",
          status: "shelved" }
  404 : 没有这个取件码
```

实现：`pickup_code` → `parcel` → `slot`（唯一）→ `shelf`（取 bay_no）→ `rack_row`（取 zone_id），
一条 JPQL join fetch 取完，走主键索引。

### F4 参数版本

```
GET /api/params/versions
  200 : [ { version: "1.0", createdAt, total: 27, observed: 9, publicCnt: 1, assumed: 17 } ]

GET /api/params/versions/{version}
  200 : { version, payload: [ { id, label, value, range, source, rationale } ] }
```

### F5 承运商在架统计

```
GET /api/stats/carriers?siteId=NH-TAOYUAN
  200 : [ { carrier: "顺丰", onShelf: 213, shelved: 213, picked: 87 } ]
```

SQL 形态：

```sql
SELECT c.name, COUNT(*) AS on_shelf
FROM parcel p JOIN carrier c ON c.code = p.carrier_code
WHERE p.site_id = ? AND p.status = 'shelved'
GROUP BY c.name ORDER BY on_shelf DESC;
```

---

## 四、仓储接口设计

```java
public interface PickupCodeRepository extends JpaRepository<PickupCode, PickupCodeId> {
    `Query("""
        select pc from PickupCode pc
        join fetch pc.parcel p
        join fetch p.slot s
        join fetch s.shelf sh
        join fetch sh.row r
        where pc.siteId = :siteId and pc.code = :code
        """)
    Optional<PickupCode> findDetail(String siteId, String code);
}
```

```java
public interface ParcelRepository extends JpaRepository<Parcel, String> {
    `Query("""
        select p.carrierCode as carrier, count(p) as cnt
        from Parcel p where p.siteId = :siteId and p.status = 'shelved'
        group by p.carrierCode order by count(p) desc
        """)
    List<CarrierCount> countOnShelfByCarrier(String siteId);
}
```

---

## 五、种子数据生成器

`data/research/export_mysql_seed.py` 做四件事：

1. 读 `scenarios.json` → 生成 `scenario` / `scenario_site_param` / `demand_bucket`
2. 读 `station_layouts.json` → 生成 `rack_row` / `shelf` / `slot`（48 / 240 / 19,200 行）
3. 按参数生成 2,000 条 `parcel` 与 `pickup_code`（取件码格式 `{货架号}-{层}-{四位序号}`，站内唯一）
4. 读 `param_registry.json` → 生成一条 `param_version`（payload 为 JSON 数组）

输出：`db/migration/V2__seed_base.sql`、`V3__seed_volume.sql`，并在结尾打印校验结果。

---

## 六、前端改动点

| 页面 | 组件 | 改动 |
|---|---|---|
| P1 | 新增 `PickupLookup.vue` | 输入框 + 结果卡片（站点/货架/层/位/承运商） |
| P3 | PeakView 顶部加"历史运行"下拉 | 选中后把该次运行的峰值与当前对比 |
| P4 | 工单详情的时间线 | 数据源从本地 actions 改为 `GET /events` |
| P5 | 参数版本行 | 从 `GET /api/params/versions` 读 |
| P1/P3 | 承运商小图 | `GET /api/stats/carriers` 画堆叠柱 |

所有新请求都走现有 `src/data/api.ts` 的 `getJson`：**后端不可达时返回 null，页面回落到本地数据**，
不破坏"没后端也能演示"的约定。

---

## 七、测试设计

| 层 | 用例 | 断言 |
|---|---|---|
| 单元 | 仿真守恒 | 与现有 3 个用例保持一致 |
| 单元 | 取件码生成 | 同站 2,000 条无重复；格式匹配 `^\\d{3}-\\d-\\d{4}$` |
| 集成 | 落库一次运行 | `simulation_run` +1、`sim_result` +132 |
| 集成 | 工单流转 | 每次 PATCH 增加 1 条事件；重复状态不增 |
| 集成 | 取件码查询 | 存在的返回 200 且字段齐全；不存在的 404 |
| 契约 | `scripts/api.mjs` | 从 29 条扩到 45 条 |
| 前端 | `scripts/interact.mjs` | 从 31 条扩到 38 条 |

---

## 八、容量与性能预估

| 表 | 行数 | 说明 |
|---|---|---|
| slot | 19,200 | 最大表；查询都走主键或 shelf_id 索引 |
| parcel / pickup_code | 2,000 | 演示抽样 |
| demand_bucket | 396 | 三场景合计 |
| sim_result | 132 × 运行次数 | 跑 100 次约 1.3 万行，仍在百万级以下 |

单表最大 2 万行，MySQL 单实例绰绰有余；不需要分区、不需要读写分离。
