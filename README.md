# 驿链 CampusFlow · 中国矿业大学南湖校区校园物流管理系统

Java 语言及网络编程课程结课作业。**前后端分离**：Vue 3 + TypeScript 前端，Spring Boot 3.2.3 + H2 后端。

> 页面上的到件量、取件需求、库存、占用率**全部是演示数据**，不是学校真实业务数据。
> 只有站点位置、营业时间、货架数量与取件码规则来自公开资料与实景照片，每处在页面上都有标签区分。

---

## 一、跑起来（两步）

### 1. 后端（端口 8080）

```bash
cd backend
mvn -DskipTests package        # 首次会联网下载依赖
java -jar target/campusflow-1.0.0.jar
```

启动后可访问：

| 地址 | 说明 |
|---|---|
| http://127.0.0.1:8080/api/health | 健康检查 |
| http://127.0.0.1:8080/api/sites | 四个站点（H2 表 site） |
| http://127.0.0.1:8080/api/scenarios | 三场景逐桶数据（12 万字节） |
| http://127.0.0.1:8080/api/workorders | 工单列表（H2 表 work_order） |
| http://127.0.0.1:8080/api/layouts/NH-TAOYUAN | 桃苑室内布局 |
| http://127.0.0.1:8080/h2-console | H2 控制台（JDBC URL: `jdbc:h2:file:./data/campusflow`，用户 sa，密码空） |

### 2. 前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

打开 http://127.0.0.1:5173/ 。`/api` 已代理到 8080：
后端在跑时右上角显示 **接口数据**，没跑时自动回落内置样例并显示 **演示数据模式**，页面功能不受影响。

---

## 二、这一版做了什么

### 数据口径（v2，2026-11-03 重算）

| 项 | 旧 | 新 |
|---|---|---|
| 待取上限 κ_i | 2,372（反推，占物理储位 12%） | **16,320**＝物理储位 19,200 × 85% |
| 日初存量 i0 | 279（几乎空仓起步） | **14,268**（双十一第 7 天早上） |
| 场景视角 | 普通的一天 | **双十一第 7 天**（第 8—9 天外推） |
| 风险判据 | 库存 > κ_i | **占用率分级**：<70% 正常 / 70–85% 预警 / 85–100% 限流 / >100% 满仓 |
| 新增指标 | — | **通道可通行率**、**高峰排队时长** |

三场景结果：

| 场景 | 桃苑占用 | 松苑 | 梅苑 | 兰苑 | 桃苑排队 |
|---|---|---|---|---|---|
| S1 常态工作日 | 2.7% | 17.9% | 17.0% | 17.6% | 16 min |
| S2 双十一第 7 天 | **83.4% 预警** | 100.4% 满仓 | 97.7% 限流 | 96.1% 限流 | 59 min |
| S3 第 7 天 + 分流增能 | 84.1% 预警 | 98.5% 限流 | 95.9% 限流 | 94.4% 限流 | **19 min** |

新增「本周与推演」面板：D1 21.6% → **D7 82.0%** → D9 97.4%（外推）。

### 前后端

- 后端：Spring Boot 3.2.3 + JPA + H2 文件库，站点与工单落表；`POST /api/simulation/run` 在服务端复算 Q/I/S/P 并返回守恒校验后的逐桶结果
- 后端测试：`mvn test` 3 个用例（手算三桶、50 组随机输入守恒、指标单调性）
- 前端：五页 + 双底图地图 + 地图校准；数据层双源（接口优先、样例兜底）

---

## 三、测试与自检

```bash
# 后端
cd backend && mvn test

# 前端（需先 npm run dev）
cd frontend
node scripts/interact.mjs                    # 31 条交互断言
node scripts/keyboard.mjs                    # 9 条键盘可达性
node scripts/calibrate.mjs                   # 20 条地图校准
node scripts/audit.mjs http://127.0.0.1:5173 1440 dark
```

当前结果：交互 31/31、键盘 9/9、校准 20/20、布局审计 0 裁剪 0 重叠、控制台 0 错误；后端 3/3。

---

## 四、还没做完的（如实列出）

1. **室内平面图的页面组件**：数据和预览图已经生成（`data/geo/station_layouts.json`、
   `docs/screenshots/桃苑室内布局-v7-收窄.png`），但还没接进站点抽屉；货架点选、储位矩阵、货架正面 2D 也还没做。
2. **P6 运输与轨迹页**：路网图与 Dijkstra 已验证可行（615 节点 / 647 边，四站里程 829/948/1775 m），
   兰苑当前在 OSM 路网中不连通需补连接段；页面未实现。
3. **前端工单仍走本地生成**：后端已有 `/api/workorders` 与状态流转，但站点抽屉与异常页还没切过去。
4. **兰苑室内布局**：等实景照片。

## 五、目录

```
backend/            Spring Boot 工程（Java 21，Maven）
frontend/           Vue 3 + Vite 工程
data/
  demo/scenarios.json        三场景逐桶数据（生成脚本 data/research/generate_demo_scenarios.py）
  geo/station_layouts.json   室内布局数据（生成脚本 data/research/gen_station_layout.py）
  params/param_registry.json 27 项参数：9 实测 / 1 公开 / 17 假设
  reference/taoyuan_interior/ 桃苑实景照片与结构化读数
docs/screenshots/   验收截图
report/             课程报告（docx）与生成脚本
```

## 六、素材与许可

OpenStreetMap 数据遵循 ODbL-1.0；卫星影像走 Esri 公共服务，仅在线使用。
实景照片为用户本人拍摄，仅用于本项目课程演示，对外发布需本人同意。
