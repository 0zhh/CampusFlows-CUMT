# 南湖校区驿链项目资料库

采集与核验日期：2026-10-27。范围仅为中国矿业大学南湖校区。

本目录保存公开资料、结构化摘录、地图与来源记录，供后续课程演示开发使用。**已经有真实校园与站点资料；尚未取得各站真实库存、面积、货架总数、库容、人员与业务流水。**

## 先读哪些文件

| 文件 | 内容 |
|---|---|
| [资料核验与缺口](资料核验与缺口.md) | 可采用结论、来源差异、待确认内容和使用边界 |
| [nanhu_sites.json](nanhu_sites.json) | 桃／松／梅／兰四个实体站；桃苑内顺丰／京东与独立收发室补充服务 |
| [nanhu_sites.csv](nanhu_sites.csv) | 四站简表；UTF-8 BOM编码，可用Excel查看；空白容量表示未知 |
| [nanhu_operating_rules.json](nanhu_operating_rules.json) | 服务流程、常态／特定年份规则、冲突处理 |
| [nanhu_warehouse_evidence.json](nanhu_warehouse_evidence.json) | 仓储结构的证据与缺口，未核实字段留null |
| [nanhu_visual_evidence.json](nanhu_visual_evidence.json) | 实拍逐图归属、可见细节、不能证明的内容与四站覆盖情况 |
| [实景素材索引](reference/实景素材索引.md) | 已降为背景参考的室内／室外照片与来源；尚无合格的完整布局资料 |
| [nanhu_public_statistics.json](nanhu_public_statistics.json) | 带时期和限制条件的历史公开数据 |
| [source_catalog.json](source_catalog.json) | 已采用来源的网页URL、日期、落盘状态和哈希 |
| [assets_catalog.json](assets_catalog.json) | A01—A11原始地图照片的来源、尺寸、哈希与使用限制 |
| [用户决策](research/user_decisions.json) | 用户已确认采用的演示规则与待答复问题 |

## 地图与照片

- [四站标注生活区地图](maps/cumtlive_logistics_locations.png)：学生手册原图，1821×1123。
- [学校发布的校园全图](maps/cumt_official_campus_traffic_2025.png)：来自2025-12-16学校公告，1262×631；其考试交通安排不是日常物流规则。
- [地图清单](maps/map_manifest.json)与[四站像素坐标](maps/logistics_markers.json)：供前端叠加点位使用，无经纬度、路网或测距保证。
- [南湖校区矢量底图](geo/cumt_nanhu_campus.geojson)：从 OpenStreetMap 经 Overpass API 抓取，299 个要素（45 栋建筑 / 227 段道路 / 8 处水系 / 16 处场地 / 3 处设施），含经纬度，ODbL-1.0 许可，署名即可用。
- [四站两套坐标](geo/site_geolocation.json)：图像像素坐标（对原图红点读取，误差≤1px）与 OSM 近似经纬度（演示近似，约±150m），两者不可互换。
- [无人站历史照片](reference/cumt_2022_unmanned_station_photo.jpg)：2022官方照片拼图，上方分别标有松苑站、兰苑站；局部设施照片不等于完整内部平面图。
- [取件指引原图](reference/cumtlive_pickup_guide.png)：收货密令操作参考图，不作为本项目真实扫码／下单功能。
- [收发室门面照片](reference/cumtlive_mailroom_notice.jpg)：只支持门面外观，不能据此认定营业时间。
- `reference/cumt_2025_logistics_photo_campus_unconfirmed.png`：两校区综合报道中的照片，画面有近邻宝标识，**校区归属未核实，禁止标为桃苑或其他南湖站内部结构**。
- `reference/cumt_2026_winter_logistics_page4.png`、`cumt_2025_winter_logistics_page4.png`：从学校原始PDF第4页渲染的可视核对页。
- 追加检索取得A07—A11：2024南湖物流园室外临时大件区、2024参观物流园内景、2023志愿者室外分拣两图、2024寒假物流货架通道内景。每张的归属限制见[实景素材索引](reference/实景素材索引.md)；没有取得完整平面图。

地图、照片保留原作者／权利人权益与来源。未核得开放授权，不应将素材重新宣称为原创或默认可商业再发布。

## 目录分工

```text
data/
  baseline/       历史基线：原规划v1.1（软件工程规范版）、v1.2（轻量前端版）
  sources/        公开页面HTML、提取TXT、官方原始PDF
  maps/           实际地图、地图元数据、像素标记
  geo/            OSM 矢量底图与四站两套坐标
  reference/      公开照片、指引图、PDF核对页
  demo/           独立的模拟数据目录，目前只有空场景模板
  research/       下载清单、研究记录、用户决策、校验及复现脚本
```

## 数据使用约定

1. `source_ids`对应`source_catalog.json`，资产编号A01等对应`research/downloads.json`。
2. 学校新闻证明的是报道时信息；学生手册是学生维护资料，不升级为正式校规。
3. 常态时间已按用户指示采用手册：桃苑08:30—18:30、三个无人站07:00—23:30。取件服务时间不证明后台分拣排班。
4. 官方具体日期通知覆盖该时段的常态参考值；不自动推及其他年份。
5. 未知值用null或CSV空白，不能转换为0或自行“合理补齐”。
6. 以后编写的演示流量、库容、处理能力放到`demo/`并标`SIMULATED`，不放进公开资料字段。
7. 地图像素点只绑定指定原图；不得当作GPS或跨图复用。
8. `sources/`用于本地研究留证，前端只打包需要的地图、精选数据与来源链接，不整包发布所有原始网页。

## 可复现性与校验

本轮使用现有Python及Codex已附带的Pillow、pypdf、Poppler，未安装新依赖。

`research/collect_sources.py`可按明确列表重新下载公开来源，`--ids S01 A01`可只更新指定项；网页可能变化、失效或要求验证，重新下载后须重新检查内容，不能只凭HTTP200判成功。

`research/build_reference_data.py`生成经过人工审阅的结构化资料，`research/validate_bundle.py`检查链接引用、哈希、图片、未知值与数据边界；运行结果保存在`research/validation_report.json`。这些是资料整理工具，不属于未来应用功能。

原始下载文件的哈希记录在`research/downloads.json`；整个交付目录文件清单记录在`research/file_manifest.json`。外部网址恢复可达不自动表示旧资料已经更新。
