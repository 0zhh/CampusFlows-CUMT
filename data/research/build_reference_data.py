"""Build a provenance-aware reference bundle from reviewed public sources.

This script writes curated research data, not measured warehouse inventory.
Run from the project root with the bundled Python runtime (Pillow/pypdf).
"""
from pathlib import Path
from PIL import Image
import csv
import hashlib
import json

DATA = Path(__file__).resolve().parents[1]
DATE = "2026-10-27"


def write_json(path, value):
    target = DATA / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def evidence(source_ids, classification, note=None):
    return {"source_ids": source_ids, "classification": classification, "note": note}


source_info = [
    ("S01", "物流服务", "CUMT生存手册（学生自发维护）", "student_guide", None, "2026-10-19", "位置、常态营业时间、取寄件流程、服务分工；页面显示更新日期不等于逐项事实核验日期。"),
    ("S02", "矿大地图快速上手", "CUMT生存手册（学生自发维护）", "student_guide", None, "2026-10-19", "宿舍苑区、食堂与校园地标；文字导览，不是测绘底图。"),
    ("S03", "[校管]我校南湖菜鸟驿站喜获双项荣誉", "中国矿业大学总务部", "official_news", "2025-04-10", None, "1+3 网络、报道时日均快递件量突破12000件、无人快递超市占比约65%；不能当作2026实时数据。"),
    ("S04", "[校管]优化升级无人快递超市，打通快递最后一百米", "中国矿业大学总务部", "official_news", "2022-07-30", None, "桃苑主站与松、梅、兰辅站；历史改建与照片；历史24小时自助服务不可直接覆盖新指南时间。"),
    ("S05", "中国矿业大学2026年寒假期间后勤服务保障工作安排", "中国矿业大学总务部", "official_period_notice", None, None, "仅适用2026寒假；第4页物流表，第2页收发室值班；发布日期未从页面核得。"),
    ("S06", "中国矿业大学2025年寒假期间后勤服务保障工作安排", "中国矿业大学总务部", "official_period_notice", "2025-01-15", None, "2025寒假历史安排，不能套用于2026常态或2027寒假。"),
    ("S07", "2025年暑期后勤服务保障", "中国矿业大学总务部", "official_news", "2025-08-25", None, "南湖暑期日均2000单；文章同时涉及文昌，照片不能全部归于南湖。"),
    ("S08", "校园地图入口（未成功下载）", "中国矿业大学师生事务服务相关站点", "official_link_unavailable", None, None, "索引可检索但本机TLS读取失败，不作为已落盘地图证据。"),
    ("S09", "校园地图", "中国矿业大学信息化建设与管理处", "official_map_index", "2023-07-03", None, "列出学校虚拟校园入口；入口日期来自列表，不代表地图测绘日期。"),
    ("S10", "2026年全国硕士研究生招生考试中国矿业大学考点考前公告", "中国矿业大学研究生招生网", "official_notice_with_map", "2025-12-16", None, "校园全图附件的官方出处；图上考试交通箭头仅适用于2025年12月相关考试。"),
    ("S11", "南湖校区规划平面图", "中国矿业大学基建与修缮处", "official_historical_map_page", "2020-12-04", None, "规划图页面已保存，原始大图未下载；规划图不能替代当前实景或当前驿站分布。"),
    ("S12", "[校管]校园管理中圆满完成迎新工作任务", "中国矿业大学总务部", "official_news_with_identified_photo", "2024-09-04", None, "明确标注南湖物流园的室外大件临时存放区照片；不能当作室内固定仓库。"),
    ("S15", "南京大学后勤服务集团来总务部调研交流", "中国矿业大学总务部", "official_news_with_interior_photo", "2024-01-06", None, "参观物流园室内照片，可见编号货架、通道、梁柱、消防设施；图注未注明桃／松／梅／兰具体站点。"),
    ("S16", "我院举办雷锋精神入我心、助力驿站畅通行活动", "中国矿业大学电气工程学院", "official_volunteer_news", "2023-03-09", None, "两张室外柜旁分拣照片，柜体可见桃苑字样；不是主站室内全景或扫码出口图。"),
    ("S17", "2023上好大学：中国矿业大学", "扬子晚报／紫牛新闻（搜狐转载页）", "media_republication_historical", "2023-06-29", None, "文字提到桃苑能容纳上百个货架，仅为历史定性量级描述，不是实测货架清单；未取得有用的站内配图。"),
    ("S18", "寒冬有暖意 后勤再蓄力：2024年寒假后勤服务保障", "中国矿业大学总务部", "official_news_with_interior_photo", "2024-02-13", None, "保障物流供给配图可见货架和通道；文章涉及两校区，未逐图注明具体站点，不能据此强行归入某一南湖站。"),
]
downloads = json.loads((DATA / "research/downloads.json").read_text(encoding="utf-8"))
download_by_id = {row["id"]: row for row in downloads}
sources = []
for identifier, title, publisher, kind, published, updated, scope in source_info:
    raw = download_by_id[identifier]
    sources.append({"id": identifier, "title": title, "publisher": publisher, "source_type": kind,
                    "url": raw["url"], "published_date": published, "page_displayed_updated_date": updated,
                    "retrieved_at": raw["retrieved_at"], "download_status": raw["status"],
                    "local_path": raw["local_path"] if raw["status"] == "downloaded" else None,
                    "sha256": raw.get("sha256"), "use_scope": scope})
write_json("source_catalog.json", {"research_date": DATE, "timezone": "Asia/Shanghai", "sources": sources})

site_specs = [
    ("NH-TAOYUAN", "桃苑物流服务中心", "桃苑菜鸟驿站／南湖物流园主站", "main_hub", "桃苑4号楼楼下南侧", "桃苑", "08:30", "18:30", [1396, 518],
     ["普通快递代收与领取", "部分大件／异形件接收", "人工查件", "普通快递服务点寄件"],
     "顺丰与京东的服务柜台位于主站内部西侧；不再计作两个独立仓储站点。"),
    ("NH-SONGYUAN", "松苑无人菜鸟驿站", "松苑无人快递超市", "unmanned_satellite", "松苑1号楼南侧，面向二食堂", "松苑", "07:00", "23:30", [839, 298],
     ["部分中小件代收", "自助取件"], "不将主站的人工寄件服务复制成本站已核实服务。"),
    ("NH-MEIYUAN", "梅苑无人菜鸟驿站", "梅苑无人快递超市", "unmanned_satellite", "梅苑1号楼北侧，面向竹苑4号楼", "梅苑", "07:00", "23:30", [378, 577],
     ["部分中小件代收", "自助取件"], "学生指南建议竹苑同学可寄往梅苑；这不是经测绘确认的排他服务边界。"),
    ("NH-LANYUAN", "兰苑无人菜鸟驿站", "兰苑无人快递超市", "unmanned_satellite", "兰苑1号楼南侧，面向兰苑2号楼", "兰苑", "07:00", "23:30", [229, 978],
     ["部分中小件代收", "自助取件"], "面向周边取件需求，不推断其每日件量或容量。"),
]
sites = []
for identifier, name, aliases, kind, location, area, opening, closing, xy, services, note in site_specs:
    sites.append({
        "id": identifier, "name": name, "aliases": aliases.split("／"), "campus": "中国矿业大学南湖校区",
        "physical_site": True, "network_role": kind, "dormitory_area": area,
        "location": {"description": location, "longitude": None, "latitude": None,
                     "evidence": evidence(["S01"], "student_reported", "楼栋方位有公开指南依据，尚未现场核验或测绘。")},
        "existence_evidence": evidence(["S01", "S03", "S04", "S05"], "cross_checked_public_sources"),
        "normal_service_hours": {"open": opening, "close": closing, "timezone": "Asia/Shanghai",
                                 "days": "指南未单列工作日／周末差异", "valid_from": None, "valid_until": None,
                                 "demo_baseline_decision_id": "USER-001",
                                 "evidence": evidence(["S01"], "student_reported", "作为演示常态资料值；不保证调查日现场实际营业状态。")},
        "confirmed_service_descriptions": services, "service_evidence": evidence(["S01"], "student_reported"),
        "warehouse_measured": {"area_m2": None, "rack_count": None, "storage_capacity_parcels": None,
                               "handling_capacity_per_hour": None, "worker_count": None, "floor_plan": None},
        "warehouse_data_status": "not_publicly_verified", "note": note,
        "map_marker": {"map_id": "MAP-LOGISTICS", "x_px": xy[0], "y_px": xy[1],
                       "coordinate_system": "image_pixels_top_left_origin", "accuracy": "approximate_source_red_dot"},
    })
service_points = [
    {"id": "NH-SF", "name": "顺丰（驿收发）", "kind": "courier_counter", "parent_site_id": "NH-TAOYUAN", "independent_physical_site": False,
     "location": "桃苑物流服务中心内部西侧", "separate_counter_hours": None, "source_ids": ["S01"],
     "pickup_method": "依短信取件码领取，异常时向现场人员询问。", "note": "不能将主站参考时间直接当作柜台已核实营业时间。"},
    {"id": "NH-JD", "name": "京东（矿大南湖小蜜蜂）", "kind": "courier_counter", "parent_site_id": "NH-TAOYUAN", "independent_physical_site": False,
     "location": "桃苑物流服务中心内部西侧", "separate_counter_hours": None, "source_ids": ["S01"],
     "pickup_method": "依短信取件码领取，异常时向现场人员询问。", "note": "独立柜台时间和柜内布局未公开核实。"},
    {"id": "NH-MAILROOM", "name": "南湖校区收发室", "kind": "postal_mailroom", "parent_site_id": None, "independent_physical_site": True,
     "part_of_cainiao_one_plus_three": False, "location": "竹苑3号楼一层南侧，三食堂斜对面", "source_ids": ["S01"],
     "normal_hours": {"weekdays": [["08:30", "11:30"], ["13:00", "17:30"]], "weekends": [["08:30", "11:30"]]},
     "services": ["平信、挂号信、明信片、印刷品、报刊等邮件领取", "部分EMS邮件领取，以实际通知为准"],
     "note": "补充服务点，不并入四站仓储容量汇总；EMS包裹与邮政收发室的具体分流以实际通知为准。"},
]
write_json("nanhu_sites.json", {"schema_version": "1.0", "research_date": DATE, "campus_scope": "CUMT_NANHU_ONLY",
                               "physical_cainiao_site_count": 4, "sites": sites, "supplementary_service_points": service_points,
                               "coverage_note": "公开资料确认的核心网络，不声称覆盖全部临时取件点或此后新增点。"})

rules = [
    {"id": "RULE-001", "subject": "常态服务结构", "description": "桃苑为主站，松苑、梅苑、兰苑为辅站。", "source_ids": ["S01", "S03", "S04", "S05"], "type": "publicly_cross_checked"},
    {"id": "RULE-002", "subject": "菜鸟自助取件", "description": "按取件通知找件，在自助设备扫描快递条码与取件码；可依指南向人工服务处求助。", "source_ids": ["S01"], "type": "student_reported"},
    {"id": "RULE-003", "subject": "顺丰／京东", "description": "在桃苑主站内部西侧服务区领取，不按四个菜鸟站任意分配。", "source_ids": ["S01"], "type": "student_reported"},
    {"id": "RULE-004", "subject": "包裹类型", "description": "主站接收部分大件与异形件；三辅站主要处理中小件。超大件是否入校需实际协调。", "source_ids": ["S01"], "type": "student_reported"},
    {"id": "RULE-005", "subject": "高峰分流", "description": "指南称开学、618、双十一时实际取件站可能与所填地址不同；演示可据此呈现分流设想，不能宣称掌握现行调度算法。", "source_ids": ["S01"], "type": "student_reported"},
    {"id": "RULE-006", "subject": "普通寄件", "description": "可在菜鸟下单选择服务点自寄或上门取件；服务点自寄前往桃苑前台。", "source_ids": ["S01"], "type": "student_reported"},
    {"id": "RULE-007", "subject": "顺丰／京东寄件", "description": "可提前在相应小程序／APP下单，选择到服务点或上门；课程演示不提交真实订单。", "source_ids": ["S01"], "type": "student_reported"},
    {"id": "RULE-008", "subject": "邮政业务", "description": "收发室承担邮件领取；指南所列部分邮寄业务需到校外邮政网点办理，EMS寄件另列上门方式。", "source_ids": ["S01"], "type": "student_reported"},
    {"id": "RULE-009", "subject": "停留时限", "description": "未核得正式免费存放天数与超期退回政策；不得将学生经验描述固化为承诺。", "source_ids": ["S01"], "type": "unverified_policy"},
    {"id": "RULE-010", "subject": "竹苑与杏苑", "description": "指南明确竹苑无独立菜鸟驿站；本轮未核得杏苑独立快递站。不得按每苑一站自动补造站点。", "source_ids": ["S01", "S02", "S04", "S05"], "type": "bounded_research_conclusion"},
]
overrides = [
    {"id": "HOURS-2026-WINTER-MAIN", "site_ids": ["NH-TAOYUAN"], "start_date": "2026-01-15", "end_date": "2026-02-25", "status": "open", "hours": [["09:00", "17:00"]], "source_ids": ["S05"], "page": 4,
     "note": "通知未在该行另列春节停业日期，不从2025通知迁移停业日期。"},
    {"id": "HOURS-2026-WINTER-SATELLITES", "site_ids": ["NH-SONGYUAN", "NH-MEIYUAN", "NH-LANYUAN"], "start_date": "2026-01-15", "end_date": "2026-02-25", "status": "closed", "hours": [], "reopen_date": "2026-02-26", "source_ids": ["S05"], "page": 4,
     "note": "官方写暂停营业，不能自动解释成仍可取件。"},
    {"id": "HOURS-2025-WINTER-MAIN", "site_ids": ["NH-TAOYUAN"], "start_date": "2025-01-20", "end_date": "2025-02-23", "status": "open_with_exception", "hours": [["09:00", "17:00"]], "closed_dates": [["2025-01-28", "2025-02-04"]], "source_ids": ["S06"], "page": 4},
    {"id": "HOURS-2025-WINTER-SATELLITES", "site_ids": ["NH-SONGYUAN", "NH-MEIYUAN", "NH-LANYUAN"], "start_date": "2025-01-20", "end_date": "2025-02-23", "status": "closed", "hours": [], "source_ids": ["S06"], "page": 4},
]
write_json("nanhu_operating_rules.json", {"research_date": DATE, "timezone": "Asia/Shanghai", "rules": rules,
    "dated_overrides": overrides, "precedence": ["同一时段的明确官方通知", "常态学生指南资料值", "历史资料仅供背景"],
    "conflicts": [
        {"id": "CONFLICT-001", "topic": "无人站开放时间", "source_ids": ["S04", "S01"], "observations": ["2022报道提到24小时自助取件", "学生指南列07:00至23:30"], "decision": "演示常态采用较新指南值并展示来源，不宣传当前24小时开放。"},
        {"id": "CONFLICT-002", "topic": "假期无人站取件", "source_ids": ["S01", "S05", "S06"], "observations": ["学生指南概述假期不收件但可取件", "2025／2026具体寒假通知写暂停营业"], "decision": "具体官方假期场景按对应年份通知；其他假期状态保持未核实，不推出全年规则。"},
        {"id": "CONFLICT-003", "topic": "2025暑期报道物流照片归属", "source_ids": ["S07"], "observations": ["报道同时涉及两校区，物流照片显示近邻宝品牌"], "decision": "该照片校区未核实，禁止标注为桃苑或南湖任一站内部布局。"},
    ]})

write_json("nanhu_public_statistics.json", {"research_date": DATE, "records": [
    {"id": "STAT-001", "metric": "日均快递件量", "value": 12000, "operator": ">", "unit": "件/日", "scope": "南湖菜鸟驿站相关公开汇总；原文未细化统计边界或每站口径", "period": "2025-04-10报道时", "source_ids": ["S03"], "allowed_use": "项目背景的历史公开量级", "forbidden_use": "当作桃苑独站件量、当前库存、当前实时到件量或每站分配量"},
    {"id": "STAT-002", "metric": "无人快递超市快递占比", "value": 65, "operator": "approximately", "unit": "%", "scope": "无人快递超市合计，未公开三站各自占比", "period": "2025-04-10报道时", "source_ids": ["S03"], "allowed_use": "说明辅站网络的重要性", "forbidden_use": "将65%均分后称为各站实测数据"},
    {"id": "STAT-003", "metric": "暑期日均快递处理量", "value": 2000, "operator": "reported", "unit": "单/日", "scope": "南湖校区，暑期口径", "period": "2025暑期；2025-08-25报道", "source_ids": ["S07"], "allowed_use": "历史假期与常态场景差异背景", "forbidden_use": "与2025年4月数据直接计算实际业务下降比例，或推导仓库容量"},
], "warning": "业务流量不等于库存容量；这组历史数字不能作为2026实时看板。"})

warehouse_records = []
for site in sites:
    warehouse_records.append({"site_id": site["id"], "site_name": site["name"],
        "publicly_supported_structure": "主站内有人工服务及快递品牌服务分区" if site["network_role"] == "main_hub" else "无人快递超市形式，面向中小件自助领取",
        "source_ids": ["S01", "S04"],
        "historical_photo_evidence": ["A04"] if site["id"] in ("NH-SONGYUAN", "NH-LANYUAN") else [],
        "measured_fields": site["warehouse_measured"],
        "unverified_details": ["精确室内平面与尺寸", "总货架数、层数与储位编号体系", "处理区与待取区真实容量", "实际人员数与处理吞吐", "当前库存和逐时段进出库流水"],
        "use_boundary": "照片及服务描述不构成可复建的室内测绘图；不得按照片可见货架推算总容量。"})
write_json("nanhu_warehouse_evidence.json", {"research_date": DATE, "status": "public_structure_partial_numeric_capacity_unknown", "records": warehouse_records,
    "visual_evidence_index": "nanhu_visual_evidence.json",
    "photo_notes": {"A04": "2022官方拼图上部标有松苑站和兰苑站，下部货架／设备局部未逐张标明站点；只能说明当时存在相应设施。", "A06": "2025两校区综合报道照片，校区与站点归属未核实，不用于南湖站点布局。", "A07": "2024南湖物流园室外高峰临时大件区，不是室内平面图。", "A08": "2024官方参观物流园内景；用户认为布局信息过少，降为背景参考，不继续要求认站。", "A09/A10": "2023室外快递柜旁的分拣实景，非室内货架布局。", "A11": "2024寒假报道货架通道内景，具体校区／站点未在图注中明确。"},
    "next_evidence_needed": ["用户现场确认各站位置与最新营业告示", "经允许拍摄的非个人敏感信息场景照片", "运营方愿意提供的面积、货架和容量汇总；没有则继续使用独立标注的演示假设"]})

map_assets = []
for map_id, asset_id, source_ids, description, allowed in [
    ("MAP-LOGISTICS", "A01", ["S01"], "学生手册四站标注生活区底图", "站点分布展示与图像坐标标记；不作精确导航、测距或地理坐标换算。"),
    ("MAP-CAMPUS", "A05", ["S10"], "学校发布的南湖校区校园全图及考试交通导引", "校园整体空间背景；考试箭头不可当作日常物流车辆通行规则。"),
]:
    raw = download_by_id[asset_id]
    image = Image.open(DATA / raw["local_path"])
    map_assets.append({"id": map_id, "asset_id": asset_id, "source_ids": source_ids, "local_path": raw["local_path"], "description": description,
                       "width_px": image.width, "height_px": image.height, "sha256": raw["sha256"], "coordinate_system": "image_pixels_top_left_origin",
                       "georeferenced": False, "map_survey_date": None, "allowed_use": allowed, "license": "rights_retained_by_original_owner; no open reuse license verified"})
write_json("maps/map_manifest.json", {"research_date": DATE, "maps": map_assets, "historical_map_page_source": "S11"})
write_json("maps/logistics_markers.json", {"map_id": "MAP-LOGISTICS", "image_width": 1821, "image_height": 1123,
    "coordinate_system": "image_pixels_top_left_origin", "method": "从原图已有红色站点标记读取的近似像素位置，非经纬度或现场GPS采样",
    "markers": [{"site_id": s["id"], "name": s["name"], "x": s["map_marker"]["x_px"], "y": s["map_marker"]["y_px"],
                 "x_ratio": round(s["map_marker"]["x_px"] / 1821, 6), "y_ratio": round(s["map_marker"]["y_px"] / 1123, 6), "source_ids": ["S01"], "asset_id": "A01"} for s in sites],
    "note": "保留原图朝向，不凭视觉假定正北方向；这些点不能直接叠加到另一张校园图。"})

with (DATA / "nanhu_sites.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["site_id", "name", "location", "reference_open", "reference_close", "hours_source", "area_m2", "capacity_parcels", "data_status"])
    for s in sites:
        writer.writerow([s["id"], s["name"], s["location"]["description"], s["normal_service_hours"]["open"], s["normal_service_hours"]["close"], "S01学生指南", "", "", "公开资料；面积容量未核实"])

write_json("demo/scenario_template.json", {"data_type": "SIMULATED_TEMPLATE", "campus": "CUMT_NANHU_ONLY", "not_real_operations": True,
    "status": "template_only_no_demo_traffic_generated", "time_step_minutes": 30, "initial_state": [
        {"site_id": s["id"], "initial_unprocessed_parcels": None, "initial_ready_for_pickup_parcels": None,
         "assumed_unprocessed_capacity": None, "assumed_pickup_inventory_capacity": None, "data_type": "SIMULATED_NOT_MEASURED"} for s in sites],
    "demand": [], "baseline_plan": None, "adjusted_plan": None,
    "note": "真实站点资料与将来人为设置的演示参数分开存放；不得将null自动转为0，未填完前不得运行仿真。"})

write_json("research/research_log.json", {"research_date": DATE, "scope": "南湖校区，四实体菜鸟站及相关服务点、地图、仓储证据与时间规则",
    "queries": ["中国矿业大学 南湖校区 快递 驿站 营业时间 菜鸟 京东 顺丰", "site:cumtlive.com 快递 地图 南湖", "site:zwb.cumt.edu.cn 南湖 校区 快递 服务中心", "site:cumt.edu.cn 2026年 菜鸟", "site:zwb.cumt.edu.cn 2026 寒假期间 物流", "site:zwb.cumt.edu.cn 2026 暑期 驿站", "中国矿业大学 南湖 校园地图 驿站 梅苑 兰苑 松苑", "site:cumt.edu.cn 南湖校区 校园平面 2026", "中国矿业大学 南湖 驿站 货架", "中国矿业大学 南湖 物流园 面积", "中国矿业大学 菜鸟 平方米", "中国矿业大学 南湖 杏苑 驿站"],
    "searched_but_not_verified": ["各站真实库容、面积、全量货架数", "当前室内测绘平面图", "四站精确经纬度与路网", "2026实时件量及人员配置", "顺丰京东各自柜台独立营业时间", "2026暑假逐站精确服务通知"],
    "retrieval_events": ["Firecrawl额度耗尽；未重试扣费调用，转用网页搜索与标准HTTP读取。", "普通urllib默认请求返回403；正常浏览器User-Agent后成功。", "学校地图服务入口S08本机TLS失败；另取得研究生招生网官方校园图A05。", "混合校区新闻图片校区归属不清，已明确禁止按南湖室内结构使用。"],
    "coverage_statement": "完成已找到公开来源的核心网络交叉核验；未完成现场调研，不宣称全量运营数据已获取。"})

write_json("research/user_decisions.json", {"date": DATE, "decisions": [
    {"id": "USER-001", "topic": "常态营业时间", "user_statement": "这个就按手册的来", "decision": "采用桃苑08:30—18:30、三个无人站07:00—23:30作为常态演示基线", "source_ids": ["S01"], "classification": "user_selected_demo_baseline", "not_a_field_measurement": True},
    {"id": "USER-002", "topic": "项目定位", "decision": "固定矿大南湖校区，课程演示优先，不建设跨高校接入平台，不要求投入真实运营", "classification": "user_scope_instruction"},
    {"id": "USER-003", "topic": "内部布局素材的有效性", "user_statement": "这种图片里面没有多少关于货架、分拣区、待取区、服务台和出入口的具体分布，有效信息少，可以不用看", "decision": "人物遮挡或仅露局部货架的照片不作为布局依据；优先完整平面图、清晰分区图或覆盖动线的连续全景资料", "classification": "user_evidence_quality_requirement"},
], "pending_questions": [
    {"id": "PENDING-001", "topic": "假期无人站是否能取已有包裹", "status": "awaiting_user_reply", "current_safe_handling": "具体年份回放按对应官方通知，其他情况标待核实"},
    {"id": "PENDING-002", "topic": "四站及桃苑内顺丰／京东有无最新搬迁或新增", "status": "awaiting_user_reply", "current_safe_handling": "按公开资料显示，保留未现场核实标签"},
]})

asset_notes = {
    "A01": (["S01"], "四站标注生活区原图", "实际公开地图，红点为原图标注，无经纬度保证"),
    "A02": (["S01"], "收货密令操作指引", "通用流程辅助，不是本项目真实取件码或扫码入口"),
    "A03": (["S01"], "南湖收发室门面", "仅说明外观，非营业告示"),
    "A04": (["S04"], "2022无人超市照片拼图", "历史松苑／兰苑入口与未逐张标站的设施局部，不作完整测绘"),
    "A05": (["S10"], "官方校园全图及考试导引", "只作校园空间背景，考试流线不作日常物流规章"),
    "A06": (["S07"], "两校区综合报道的物流服务照片", "校区未核实，禁止用作南湖任一站布局"),
    "A07": (["S12"], "2024南湖物流园临时大件区巡查实拍", "南湖与室外区域有明确图文依据；不能称为主站室内或常态固定布局"),
    "A08": (["S15"], "2024参观物流园室内实拍", "用户认为布局信息少；仅保留背景参考，不作平面布局依据，不再要求认站"),
    "A09": (["S16"], "2023志愿者室外分拣实拍之一", "画面可见桃苑柜体字样；仅支持室外柜旁区域，不是室内货架布局"),
    "A10": (["S16"], "2023志愿者室外分拣实拍之二", "与A09同场景；不能按人物或包裹数量推算运营能力"),
    "A11": (["S18"], "2024寒假货架与通道内景", "具体站点与校区未逐图注明；不直接绑定桃苑或其他南湖站"),
}
assets = []
for asset_id, (source_ids, title, restriction) in asset_notes.items():
    raw = download_by_id[asset_id]
    image = Image.open(DATA / raw["local_path"])
    assets.append({"id": asset_id, "title": title, "url": raw["url"], "source_ids": source_ids,
                   "local_path": raw["local_path"], "width_px": image.width, "height_px": image.height,
                   "sha256": raw["sha256"], "use_restriction": restriction,
                   "rights": "original_rightsholder; open_reuse_license_not_verified"})
write_json("assets_catalog.json", {"research_date": DATE, "assets": assets})

write_json("nanhu_visual_evidence.json", {"research_date": DATE, "floor_plans_obtained": [], "current_live_images_obtained": False,
    "layout_reconstruction_ready": False, "high_information_layout_asset_ids": [],
    "background_only_asset_ids": ["A04", "A07", "A08", "A09", "A10", "A11"],
    "acceptance_criteria": ["具体站点可确认", "入口、出口、服务台、分拣区、待取区及主要货架的相互位置可识别", "主要通道和盲区有覆盖", "有拍摄日期／资料适用期", "照片不足时不补造布局"],
    "description": "公开历史实拍照片，不是实时监控、最新现场核验或测绘图。", "records": [
        {"asset_id": "A04", "source_ids": ["S04"], "published_date": "2022-07-30", "kind": "exterior_and_interior_collage", "site_attribution": "松苑／兰苑门面明确，室内子图未逐张标站", "visible": ["两个站点门面", "自助设备", "多排编号货架", "货架间通道"], "not_proven": ["每张内景属于哪站", "当前布局", "完整尺寸", "总容量"]},
        {"asset_id": "A07", "source_ids": ["S12"], "published_date": "2024-09-04", "kind": "outdoor_temporary_storage_collage", "site_attribution": "南湖物流园，桃苑4号楼南侧临时区有正文与图注支持", "visible": ["大件包裹地面分区", "临时帐篷", "通道", "消防器材", "快递品牌标识"], "not_proven": ["室内布局", "常态长期分区", "实际面积"]},
        {"asset_id": "A08", "source_ids": ["S15"], "published_date": "2024-01-06", "kind": "interior_photo", "site_attribution": "中国矿业大学物流园，具体站点待确认", "visible": ["编号货架", "通道", "梁柱", "灭火器与指示牌"], "not_proven": ["具体桃／松／梅／兰归属", "完整平面", "当前仍一致"]},
        {"asset_id": "A09", "source_ids": ["S16"], "published_date": "2023-03-09", "kind": "outdoor_sorting_photo", "site_attribution": "画面柜体可辨桃苑字样，支持桃苑区域；非室内", "visible": ["快递柜", "分拣筐", "临时遮棚", "包裹分拣作业"], "not_proven": ["主站室内结构", "柜体当年与当前位置一致"]},
        {"asset_id": "A10", "source_ids": ["S16"], "published_date": "2023-03-09", "kind": "outdoor_sorting_photo", "site_attribution": "A09同场景", "visible": ["快递柜", "分拣筐", "临时遮棚"], "not_proven": ["室内结构", "完整库存"]},
        {"asset_id": "A11", "source_ids": ["S18"], "published_date": "2024-02-13", "reported_period": "2024寒假", "kind": "interior_collage", "site_attribution": "学校物流服务照片，具体校区／站点未标", "visible": ["两侧货架", "狭长通道", "货架编号", "操作终端"], "not_proven": ["南湖或文昌归属", "具体站点", "货架总数"]},
    ], "station_coverage": {"NH-TAOYUAN": "室外区域实拍已取得，独立明确标名的室内图待补", "NH-SONGYUAN": "门面明确；相关官方拼图内景未逐张标站", "NH-LANYUAN": "门面明确；相关官方拼图内景未逐张标站", "NH-MEIYUAN": "未取得能独立明确归属本站的室内实拍或平面图"},
    "unconfirmed_historical_claim": {"source_ids": ["S17"], "claim": "2023媒体文字称桃苑可容纳上百个货架", "handling": "保留为历史定性线索，不填实测rack_count，不据此换算面积或件数容量"},
    "search_limits": ["未找到可核验完整平面图／CAD", "公开视频与社交图片搜索未获得可独立确认四站归属的新增内景素材", "协会刊物PDF下载未在合理时间完成，已主动中止，未作为已取得证据"],
    "user_photo_review": {"asset_id": "A08", "status": "answered_insufficient_layout_information", "decision_id": "USER-003", "followup": "不继续要求辨认低信息照片，保留作背景资料"},
    "focused_layout_search": {"channels": ["学校总务部公开新闻", "学院活动原文", "学校采购招标与改建附件索引", "公开图片搜索", "公开视频及社交页面搜索"], "queries": ["中国矿业大学 物流园 改造 招标", "中国矿业大学 无人快递超市 图纸", "南湖 桃苑4号楼 平面图", "中国矿业大学 驿站 平面布置", "中国矿业大学 无人快递超市 全景"], "result": "本轮公开检索未取得达到用户分区布局标准的图纸、全景或连续视频，不以局部实拍替代。"}})
print("Built reference JSON, CSV, map manifest and research ledger.")
