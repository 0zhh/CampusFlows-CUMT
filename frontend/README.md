# CampusFlow / 驿链 · 前端

中国矿业大学南湖校区校园物流管理系统的**课程演示原型**前端。
Java 编程基础课程结课大作业，第 1 段交付物（F1–F6）。

> 页面上的到件量、取件需求、处理能力、库容阈值**全部是演示假设值**，
> 不是学校真实业务数据。只有站点位置、营业时间、服务项目来自公开资料。
> 每处数值都带「公开资料 / 演示假设 / 待核实」标签，三类不混用。

## 跑起来

```bash
cd frontend
npm install
npm run dev          # http://127.0.0.1:5173
```

构建与类型检查：

```bash
npm run build        # vue-tsc --noEmit && vite build
npm run preview      # 预览 dist/
```

后端还没写。`npm run dev` 时 `/api` 会代理到 `127.0.0.1:8080`，
连不上就**静默回落**到内置样例 `src/data/scenarios.json`，顶栏亮「演示数据模式」。
后端起来后自动换成接口数据，不需要改前端代码。

## 页面

| 路由 | 页面 | 内容 |
|---|---|---|
| `/overview` | 运营总览 P1 | 6 个 KPI、校区地图、四站状态、流量曲线、峰值 vs 上限、本期要点 |
| `/sites` | 站点与服务 P2 | 四站卡片、30 分钟一桶的运行表（33 行）、补充服务点、明确不建的站点 |
| `/peak` | 高峰与方案 P3 | 双库存堆叠、需求 vs 处理能力、方案对比、风险时段清单、公式 |
| `/incidents` | 异常协同 P4 | 风险工单看板、工单详情、处理记录、状态流转 |
| `/about` | 资料与说明 P5 | 数据来源、三类标签、公开统计、地图来源、模型假设、不做的内容 |

## 目录

```
src/
  components/    CampusMap（Leaflet 三层底图）、EChart、KpiCard、SiteDrawer…
  composables/   useData（数据访问）、useDataSource（后端探测）、useChartTheme、useCountUp、useReveal
  data/          types.ts、sites.ts、scenarios.json（后端 DTO 必须与此对齐）
  stores/app.ts  主题、场景、数据来源
  styles/        tokens.css（设计 token）、base.css（重置与通用类）
  views/         五个页面
public/
  geo/cumt_nanhu_campus.geojson   OSM 矢量底图，299 个要素，ODbL-1.0
  maps/cumtlive_logistics_locations.png  学生手册原图（近似配准）
scripts/         audit / interact / mapshot / text 等无头浏览器检查脚本
```

## 数据契约

`src/data/types.ts` 是前后端唯一契约。后端 DTO 的字段名、嵌套层级必须逐字一致，
否则第 3 段联调时前端要改一遍。三个场景：

- `S1-NORMAL` 常态工作日：6,200 到件 / 5,952 取走，无风险
- `S2-PEAK` 双十一高峰：13,640 到件 / 9,300 取走，桃苑 12 个风险时段
- `S3-PEAK-ADJ` 高峰 + 分流增能：13,640 到件 / 9,300 取走，零风险

站点常量 `C0 / κ_q0 / κ_i0 / I0` 只在 S2 上标定一次，三个场景共用；
场景要改这些值必须用 `cap_mult` / `kappa_q_mult` / `kappa_i_mult` 显式表达运营措施。

## 自查脚本

需要先 `npm run dev`。全部用 Chrome DevTools Protocol 驱动无头浏览器，
不靠肉眼：

```bash
node scripts/interact.mjs                    # 27 条交互断言 + 控制台错误计数
node scripts/audit.mjs http://127.0.0.1:5173 1440 dark    # 布局/裁剪/重叠/对比度
node scripts/audit.mjs http://127.0.0.1:5173 1440 light
node scripts/mapshot.mjs 1440 dark vector    # 单独截地图
node scripts/text.mjs /overview              # 导出页面可见文本
```

## 素材许可

矢量底图来自 OpenStreetMap，ODbL-1.0，署名「© OpenStreetMap contributors」已放在
地图右下角与页脚。卫星影像走 Esri 公共服务，仅在线使用、不缓存分发。
其余 11 张实景图片的再发布许可**尚未核实**，只用于课堂演示，不公开分发。
