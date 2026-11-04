# CampusFlow / 驿链 · MySQL 接入实施规划（v2）

> 版本：v2.0 · 2026-11-04
> 目标：把"H2 演示库"升级为"Docker MySQL 生产形态库"，并由此延伸出 5 个新功能。
> 前置状态：Docker 29.9.2（Docker Desktop）已就绪；MySQL 8.4.13 已在容器里跑起来。

---

## 一、容器与连接（已就绪）

| 项 | 值 |
|---|---|
| 容器名 | `campusflow-mysql` |
| 镜像 | `mysql:8.4`（实测版本 8.4.13） |
| 宿主端口 | `127.0.0.1:3307` → 容器 3306（3306 已被本机 Windows MySQL 占用，刻意避开） |
| 数据库 | `campusflow`（utf8mb4 / utf8mb4_0900_ai_ci） |
| 账号 | `root` / `__MYSQL_PASSWORD_REMOVED__`（仅演示环境） |
| 数据卷 | `campusflow-mysql-data`（命名卷，docker rm 不丢数据） |
| 时区 | `Asia/Shanghai` |
| 重启策略 | `unless-stopped` |

启动命令（已在本次执行）：

```bash
docker run -d --name campusflow-mysql --restart unless-stopped \
  -p 127.0.0.1:3307:3306 \
  -e MYSQL_ROOT_PASSWORD=__MYSQL_PASSWORD_REMOVED__ \
  -e MYSQL_DATABASE=campusflow -e TZ=Asia/Shanghai \
  -v campusflow-mysql-data:/var/lib/mysql \
  mysql:8.4 --character-set-server=utf8mb4 --collation-server=utf8mb4_0900_ai_ci
```

连接串（Spring Boot）：

```
jdbc:mysql://127.0.0.1:3307/campusflow?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false
```

> 为什么不用 3306：本机已经装了 Windows 版 MySQL Server 且占着 3306。按用户要求**不使用本机 MySQL**，
> Docker 实例固定走 3307，两者互不干扰，也避免误连到本机那一套数据。

---

## 二、两种运行形态：H2 与 MySQL 并存

| profile | 数据源 | 用途 | 启动方式 |
|---|---|---|---|
| `dev`（默认） | H2 文件库 `./data/campusflow` | 零依赖演示、答辩现场没网也能跑 | `java -jar app.jar` |
| `mysql` | Docker MySQL `127.0.0.1:3307` | 展示真实数据库能力、跑 SQL 与聚合查询 | `java -jar app.jar --spring.profiles.active=mysql` |

原则：**同一套 JPA 实体与仓储，两个 profile 只换 datasource**。
不做"两套代码"，避免 H2 与 MySQL 行为分叉。

配置落地：

- `backend/src/main/resources/application.yml`：公共配置（端口、JPA、日志）
- `application-dev.yml`：H2 连接 + `ddl-auto: update`
- `application-mysql.yml`：MySQL 连接 + `ddl-auto: validate`（表结构由 SQL 脚本建，不让 Hibernate 改表）

---

## 三、建表与种子数据

三个脚本，按顺序执行，**幂等**（可重复跑）：

| 顺序 | 文件 | 内容 | 幂等方式 |
|---|---|---|---|
| 1 | `db/migration/V1__schema.sql` | 15 张表的 DDL + 索引 + 外键 + CHECK | `CREATE TABLE IF NOT EXISTS` |
| 2 | `db/migration/V2__seed_base.sql` | site / carrier / scenario / 参数 / 工单 | `INSERT ... ON DUPLICATE KEY UPDATE` |
| 3 | `db/migration/V3__seed_volume.sql` | 逐桶需求、储位、抽样包裹与取件码 | 先 `DELETE` 再 `INSERT`（大表用事务包住） |

生成方式：`data/research/export_mysql_seed.py` 读现有 JSON（scenarios / layouts / params / sites），
产出 V2、V3 两个 SQL 文件；脚本结尾做**总量校验**：

- `demand_bucket` 行数 = 396，且 `SUM(arrivals)` 与 JSON 的 13,640（S2）一致
- `slot` 行数 = 19,200
- `shelf` 行数 = 240，其中 `managed_by = JD` 的恰好 50 个货架号

执行方式（容器内）：

```bash
docker exec -i campusflow-mysql mysql -uroot -p__MYSQL_PASSWORD_REMOVED__ campusflow < db/migration/V1__schema.sql
```

---

## 四、代码改造清单

### 4.1 后端

| 项 | 改动 |
|---|---|
| `pom.xml` | 新增 `mysql-connector-j`（`runtime`） |
| `application-mysql.yml` | 新增，见上 |
| 实体 | 由现有 2 个（Site、WorkOrder）扩到 15 个；`Site` 补 lat/lng/aisleM 等字段 |
| 仓储 | 新增 8 个 Repository，含 3 个聚合查询（按承运商、按站点、按状态） |
| 服务 | 新增 `SimulationRunService`（落库一次运行）、`PickupService`（取件码查询）、`StatsService`（聚合） |
| 控制器 | 新增 5 组接口，见《04-具体设计》§3 |
| 种子 | 新增 `MysqlSeedRunner`：`mysql` profile 下不写库（表已由 SQL 建好），只做存在性检查 |

### 4.2 前端

| 页面 | 改动 |
|---|---|
| P1 运营总览 | 加"取件码查询"输入框（调 `GET /api/pickup/{code}`） |
| P2 站点与服务 | 平面图的储位占用改为读 `GET /api/layouts/{id}/occupancy` |
| P3 高峰与方案 | 加"历史运行"下拉（`GET /api/simulations`），可对比两次运行的峰值 |
| P4 异常协同 | 工单详情的时间线改为读 `GET /api/workorders/{id}/events` |
| P5 资料与说明 | 参数版本从 `GET /api/params/versions` 读，显示"v1.0 · 9 实测/1 公开/17 假设" |

---

## 五、分阶段实施（每步可独立验收）

| 阶段 | 内容 | 验收标准 | 估时 |
|---|---|---|---|
| **P0 环境**（已完成） | Docker 起 MySQL 8.4，建库 `campusflow` | `SELECT VERSION()` 返回 8.4.13；`SHOW DATABASES` 有 campusflow | 0.5 h |
| **P1 建表** | 写 V1__schema.sql，容器内执行 | 15 张表存在；外键与唯一索引齐全 | 3 h |
| **P2 种子** | 写生成器 + V2/V3，导入 | 三张校验表行数与总量对得上 | 3 h |
| **P3 实体与仓储** | 15 个实体、8 个仓储、`mysql` profile | 应用能以 `mysql` 启动，`GET /api/sites` 返回同样的 4 条 | 6 h |
| **P4 新功能接口** | 5 组接口 + 服务 | 接口契约测试从 29 条扩到 ~45 条，全绿 | 8 h |
| **P5 前端接入** | 5 处页面改动 | 交互断言扩到 ~38 条；两套 profile 下页面表现一致 | 6 h |
| **P6 回归与文档** | 全量回归 + README + 截图 | 见 §6 验证矩阵 | 3 h |

合计约 **29.5 小时**。

---

## 六、验证矩阵

| 层次 | 检查 | 手段 | 通过标准 |
|---|---|---|---|
| 库 | 表数量 | `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=campusflow` | = 15 |
| 库 | 行数 | `SELECT COUNT(*) FROM slot` / `shelf` / `demand_bucket` | 19,200 / 240 / 396 |
| 库 | 总量 | `SELECT SUM(arrivals) FROM demand_bucket WHERE scenario_id=S2-PEAK` | = 13,640 |
| 库 | 约束 | 尝试重复插取件码 | 报 1062 重复键错误 |
| 接口 | 契约 | `scripts/api.mjs` | 45/45 |
| 前端 | 交互 | `scripts/interact.mjs` | 38/38 |
| 前端 | 双 profile | 分别在 `dev` / `mysql` 下跑 | 页面数值一致 |
| 性能 | 取件码查询 | `EXPLAIN` + 实测 | 走主键，< 10 ms |

---

## 七、回滚与风险

| 风险 | 影响 | 对策 |
|---|---|---|
| 容器被删导致数据丢失 | 演示数据没了 | 用命名卷 `campusflow-mysql-data`；SQL 脚本可重建 |
| MySQL 与 H2 行为差异（如排序、大小写） | 页面数值不一致 | `ddl-auto=validate` + 双 profile 各跑一遍断言 |
| 19,200 行储位插入慢 | 种子导入超时 | 批量 INSERT（每 1,000 行一条），事务包裹 |
| 本机 3306 上的旧 MySQL 被误用 | 数据混乱 | 连接串写死 3307，且 `127.0.0.1` 绑定 |
| 端口 3307 被占用 | 起不来 | 启动前检查；冲突则换 3308 并同步改 yml |

**回滚**：`docker stop campusflow-mysql` 后，用 `--spring.profiles.active=dev` 启动即回到 H2 形态，
前端无需改动（数据源探测会自动回落）。
