# -*- coding: utf-8 -*-
"""补齐来源目录，并生成参数注册表 data/params/param_registry.json。

设计原则（写进文件本身，任何人打开都能看懂）：
  1. 每个参数都有 source 字段，取值 observed / public / assumed
  2. assumed 必须有 range 和 rationale，否则脚本报错
  3. public 必须有 source_ids，指向 source_catalog.json
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CAT = os.path.join(ROOT, 'data', 'source_catalog.json')
PARAMS = os.path.join(ROOT, 'data', 'params', 'param_registry.json')
os.makedirs(os.path.dirname(PARAMS), exist_ok=True)

NEW_SOURCES = [
    {
        "id": "S19",
        "title": "139.38亿件！2025年“双11”期间快递业务量再创新高",
        "publisher": "新华网（转国家邮政局监测数据）",
        "source_type": "official_news",
        "url": "https://www.news.cn/fortune/20251112/c261f96ed1ca45858f1a7774c3c27d0f/c.html",
        "published_date": "2025-11-12",
        "retrieved_at": "2026-11-03T00:00:00+00:00",
        "download_status": "fetched_text_only",
        "use_scope": "双11 期间全国快递日均揽收 6.34 亿件，为日常业务量的 117.8%；单日峰值 7.77 亿件。用于给出“旺季放大倍数”的下界锚点。"
    },
    {
        "id": "S20",
        "title": "快递驿站的自助取件真的好用吗？",
        "publisher": "闽南日报（漳州新闻网）",
        "source_type": "local_news",
        "url": "http://www.zzxww.com/pc/content/202403/05/content_127924.html",
        "published_date": "2024-03-05",
        "retrieved_at": "2026-11-03T00:00:00+00:00",
        "download_status": "fetched_text_only",
        "use_scope": "取件码结构：每个货架每层有编号，取件码前两位对应货架号与层号，后四位为顺序码；自助取件先按码找件再扫码出库。用于定义储位编码与取件码生成规则。"
    },
    {
        "id": "S21",
        "title": "“人还未至，行李先到”，开学前有高校驿站每日到3万个包裹",
        "publisher": "光明网（转潇湘晨报/九派新闻）",
        "source_type": "news",
        "url": "https://m.gmw.cn/2025-09/08/content_1304139182.htm",
        "published_date": "2025-09-08",
        "retrieved_at": "2026-11-03T00:00:00+00:00",
        "download_status": "fetched_text_only",
        "use_scope": "武汉某高校南湖校区驿站开学季日均到件约 3 万件、比平时增加约 2 倍、30 人引导出库、单件派费约 0.9 元、室内不足时开辟室外临时堆放区。用于给出校园旺季放大倍数的上界锚点与人力/临时区参数。"
    },
    {
        "id": "S22",
        "title": "菜鸟驿站（百科词条）",
        "publisher": "百度百科",
        "source_type": "encyclopedia",
        "url": "https://baike.baidu.com/item/%E8%8F%9C%E9%B8%9F%E9%A9%BF%E7%AB%99",
        "published_date": None,
        "retrieved_at": "2026-11-03T00:00:00+00:00",
        "download_status": "fetched_text_only",
        "use_scope": "全国城市站点 4 万余个、高校校园驿站 1000 余个；末端“社会化协同”模式。仅作背景量级，不作本站数据。"
    },
    {
        "id": "S23",
        "title": "快递驿站专用货架 商品规格（1800×600×2000 mm，5 层，承重 300 kg）",
        "publisher": "1688 商品页（多家厂商同规格）",
        "source_type": "commercial_spec",
        "url": "https://detail.1688.com/offer/954688016157.html",
        "published_date": None,
        "retrieved_at": "2026-11-03T00:00:00+00:00",
        "download_status": "fetched_text_only",
        "use_scope": "驿站货架常见外形尺寸与层数、承重。用于平面图与储位模板的默认尺寸，不代表南湖校区的实测尺寸。"
    },
    {
        "id": "S24",
        "title": "快递暂行条例（第二十六条：无法投递的快件应当退回寄件人）",
        "publisher": "国务院",
        "source_type": "regulation",
        "url": "https://www.gov.cn/zhengce/content/2018-03/27/content_5277757.htm",
        "published_date": "2018-03-27",
        "retrieved_at": "2026-11-03T00:00:00+00:00",
        "download_status": "not_downloaded",
        "use_scope": "“超时未取 → 退回”的制度依据。具体保管天数由各站点自定，本模型取 3 天并给出 3—10 天区间。"
    }
]

cat = json.load(open(CAT, encoding='utf-8'))
have = {s['id'] for s in cat['sources']}
added = 0
for s in NEW_SOURCES:
    if s['id'] not in have:
        cat['sources'].append(s)
        added += 1
cat['research_date'] = '2026-11-03'
json.dump(cat, open(CAT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('sources: +%d, total %d' % (added, len(cat['sources'])))

PARAM_LIST = [
    # ---------- A 体量与结构 ----------
    dict(id='P-DAILY-ARRIVAL', group='A 体量', label='设计峰值日到件量（四站合计）',
         value=13640, unit='件/日', range=[11000, 16000], source='assumed',
         source_ids=['S03', 'STAT-001'],
         rationale='学校公开报道“日均 >12000 件”为全校口径；四站分摊后取 13640 作为双11场景的设计峰值。',
         used_by=['scenarios.json S2/S3'], swap_hint='拿到驿站真实日均后替换，并重跑 calibrate_norm'),
    dict(id='P-D11-MULT', group='A 体量', label='旺季相对日常的放大倍数',
         value=2.2, unit='倍', range=[1.18, 3.0], source='assumed',
         source_ids=['S19', 'S21'],
         rationale='下界 1.18 来自国家邮政局“双11日均=日常117.8%”；上界 3.0 来自高校开学季“比平时增加约2倍”。校园电商渗透高、取件集中，取中上值 2.2。',
         used_by=['scenarios.json'], swap_hint='替换后需重算 S2/S3 全部逐桶数据'),
    dict(id='P-CARRIER-SHARE', group='A 体量', label='承运商件量份额',
         value={'顺丰': 0.12, '京东': 0.10, '中通': 0.18, '圆通': 0.15, '韵达': 0.14, '申通': 0.11, '邮政EMS': 0.08, '其他': 0.12},
         unit='占比', range=[0.6, 1.6], source='assumed', source_ids=['S01'],
         rationale='按行业内常见份额排序构造；顺丰/京东份额偏高，因为两者在主站有独立服务区（公开资料支持）。区间为整体缩放。',
         used_by=['实体仿真 批次生成'], swap_hint='可由驿站公示的“各家货架数”近似反推'),
    dict(id='P-PICKUP-RATIO', group='A 体量', label='当日取件量 / 当日到件量',
         value=0.68, unit='比例', range=[0.55, 0.80], source='assumed', source_ids=['S21'],
         rationale='保管期 3 天、学生当天取件为主；0.68 与“日均积压 ≈ 32% 结转到次日”自洽，且与 S1/S2 场景的 9300/13640 一致。',
         used_by=['scenarios.json'], swap_hint='用真实出入库流水替换'),
    dict(id='P-STUDENT-POP', group='A 体量', label='南湖校区在校生规模',
         value=20000, unit='人', range=[15000, 25000], source='assumed', source_ids=['S02'],
         rationale='仅用于把“件量”换算成“人均件量”做合理性检查（13640/20000 ≈ 0.68 件/人/日，落在合理区间）。',
         used_by=['合理性检查'], swap_hint='用学校官网公开的在校生数替换'),

    # ---------- B 到车与作业 ----------
    dict(id='P-BATCH-WINDOWS', group='B 作业', label='到车时间窗口',
         value=['08:30', '12:30', '16:00'], unit='时刻', range=[-45, 45], source='assumed',
         source_ids=['S19', 'S21'],
         rationale='按“凌晨分拨、早班进城、午间补车、傍晚二次补车”的普遍节奏构造三个窗口；区间为前后 45 分钟的三角分布抖动。',
         used_by=['实体仿真 批次生成'], swap_hint='现场蹲点记录即可替换（本项属可观测字段）'),
    dict(id='P-TRUCK-LOAD', group='B 作业', label='单车装载量',
         value=[800, 1200, 1800], unit='件/车', range=[600, 2000], source='assumed', source_ids=[],
         rationale='按常见厢式货车容积与包裹平均体积反推；大站一次到车 1000—2000 件是行业常见量级。',
         used_by=['实体仿真 批次生成'], swap_hint='数一次到车件数即可替换'),
    dict(id='P-UNLOAD-RATE', group='B 作业', label='卸货+初分速度',
         value=25, unit='件/分钟/人', range=[20, 30], source='assumed', source_ids=['S21'],
         rationale='按人工卸车并粗分道的常见节拍；区间取自公开作业规范的常见范围。',
         used_by=['实体仿真 卸货'], swap_hint='现场掐表即可替换'),
    dict(id='P-STAFF', group='B 作业', label='在岗人数',
         value={'NH-TAOYUAN': 6, 'NH-SONGYUAN': 0, 'NH-MEIYUAN': 0, 'NH-LANYUAN': 0},
         unit='人', range=[4, 8], source='assumed', source_ids=['S21'],
         rationale='主站有 1 个服务台 + 分拣；三个无人站为自助扫码，无常驻人员。开学季某校驿站 30 人只用于说明峰值人力可扩张。',
         used_by=['实体仿真 卸货/服务台'], swap_hint='观察一次即可替换'),
    dict(id='P-HOLD-DAYS', group='B 作业', label='包裹保管期',
         value=3, unit='天', range=[3, 10], source='assumed', source_ids=['S24'],
         rationale='制度上“无法投递应退回”，天数由站点自定；驿站普遍 3 天短信提醒、超期退回，也有站点放宽到 7—10 天。取 3 天。',
         used_by=['实体仿真 超时退回'], swap_hint='看驿站告示即可替换'),

    # ---------- C 货架与储位 ----------
    dict(id='P-SHELF-SPEC', group='C 储位', label='货架外形尺寸',
         value={'length_mm': 1800, 'depth_mm': 600, 'height_mm': 2000, 'tiers': 5},
         unit='mm', range=[0.9, 1.1], source='public', source_ids=['S23'],
         rationale='电商平台上“快递驿站专用货架”的主流规格，多家厂商一致；本项目的平面图默认按此尺寸绘制。',
         used_by=['平面图模板'], swap_hint='换成南湖实测尺寸（会拍照补充）'),
    dict(id='P-TIERS', group='C 储位', label='货架层数（含顶层）',
         value=6, unit='层', range=[5, 7], source='assumed', source_ids=['S23'],
         rationale='5 层货架 + 顶层暂存大件；层高按 33 cm 估算，底层放大件。',
         used_by=['平面图模板', '储位分配'], swap_hint='以照片为准'),
    dict(id='P-SLOTS-PER-TIER', group='C 储位', label='每层储位数',
         value=25, unit='个', range=[20, 30], source='assumed', source_ids=['S23'],
         rationale='1.8 m 长 ÷ 约 7 cm 一件（含间隙）≈ 25；实际按包裹尺寸混排会略少。',
         used_by=['平面图模板', '储位分配'], swap_hint='以照片/实测为准'),
    dict(id='P-SLOT-CAPACITY', group='C 储位', label='单储位容量',
         value=1, unit='件', range=[1, 2], source='assumed', source_ids=[],
         rationale='中小件一格一件，便于按取件码定位；大件区按占地面积折算。',
         used_by=['储位分配'], swap_hint='—'),
    dict(id='P-CODE-FORMAT', group='C 储位', label='取件码结构',
         value='{货架}{层}-{位} + 4 位顺序码', unit='格式', range=None, source='public', source_ids=['S20'],
         rationale='公开报道明确：“取件码前两位对应货架号与层数，后四位为快递顺序码”。本项目按同构规则生成，不指向真实运单。',
         used_by=['取件码生成'], swap_hint='以驿站实际短信为准'),

    # ---------- D 服务与排队 ----------
    dict(id='P-SERVICE-TIME', group='D 服务', label='单人取件服务时长',
         value={'counter_sec': 90, 'self_sec': 25}, unit='秒/人', range=[0.7, 1.4], source='assumed',
         source_ids=['S20'],
         rationale='人工台：报码—找件—扫码—交付约 90 秒；自助：按码找件—扫码约 25 秒（不含找件时间）。区间为整体缩放。',
         used_by=['实体仿真 排队'], swap_hint='现场计时即可替换'),
    dict(id='P-PICKUP-CURVE', group='D 服务', label='取件时段分布',
         value=[0.02, 0.05, 0.10, 0.13, 0.10, 0.08, 0.07, 0.08, 0.12, 0.14, 0.07, 0.04],
         unit='占日取件比例（08:00 起每 1.5 小时一格）', range=[0.6, 1.4], source='assumed',
         source_ids=['S21'],
         rationale='课间与晚饭后两个峰（12:00 与 18:00 前后），上午偏低；区间为整体缩放。',
         used_by=['实体仿真 取件'], swap_hint='用驿站出库流水替换'),
    dict(id='P-PICKUP-DELAY', group='D 服务', label='取件延迟分布',
         value={'same_day': 0.60, 'next_day': 0.30, 'overdue': 0.10}, unit='比例', range=[0.5, 0.7],
         source='assumed', source_ids=['S24'],
         rationale='当天取为主，次日次之；超过保管期进“超时退回”流程。',
         used_by=['实体仿真 取件'], swap_hint='用真实取件时间戳替换'),

    # ---------- E 运输 ----------
    dict(id='P-VEHICLE-SPEED', group='E 运输', label='校内配送平均速度',
         value=15, unit='km/h', range=[10, 20], source='assumed', source_ids=[],
         rationale='电动三轮车新国标限速 25 km/h，校内需避让学生、过减速带，平均取 15 km/h。',
         used_by=['实体仿真 路径时间'], swap_hint='实测一次到车行驶时间即可替换'),
    dict(id='P-VEHICLE-LOAD', group='E 运输', label='配送车单次载量',
         value={'kg': 300, 'parcels': 120}, unit='kg / 件', range=[0.7, 1.3], source='assumed',
         source_ids=[], rationale='三轮车常见载重 300 kg；按平均 2.5 kg/件折算约 120 件。',
         used_by=['实体仿真 转运'], swap_hint='—'),
    dict(id='P-ROUTE-GRAPH', group='E 运输', label='院内路网图规模',
         value={'nodes': 615, 'edges': 647}, unit='个', range=None, source='observed',
         source_ids=['S02'],
         rationale='由本项目从 OSM 道路中心线构建并实测（probe_route_graph.py）。四站里程 829/948/1775/— m。',
         used_by=['实体仿真 路径'], swap_hint='换成学校官方路网或实测轨迹'),
    dict(id='P-LANYUAN-LINK', group='E 运输', label='兰苑连接段（补绘）',
         value=60, unit='m', range=[40, 120], source='assumed', source_ids=[],
         rationale='现有 OSM 路网中兰苑不与主网连通，补一条约 60 m 的连接段；数据里标注“补绘”，不是实测。',
         used_by=['实体仿真 路径'], swap_hint='用真实路网替换后删除本参数'),
]

# 校验
for p in PARAM_LIST:
    if p['source'] == 'assumed':
        assert p.get('range') is not None, p['id'] + ' 缺 range'
        assert p.get('rationale'), p['id'] + ' 缺 rationale'
    if p['source'] == 'public':
        assert p.get('source_ids'), p['id'] + ' 缺 source_ids'

out = {
    'version': '1.0',
    'generated_at': '2026-11-03',
    'policy': {
        'source_levels': {
            'observed': '本项目现场/脚本实测，样本与误差写在 rationale 里',
            'public': '公开可检索资料，必须给 source_ids',
            'assumed': '演示假设，必须给 range 与 rationale'
        },
        'rule': '页面上三种标签不得混用；结论只用相对量表述；真实数据到手后只改本文件，不改代码'
    },
    'count': len(PARAM_LIST),
    'stats': {
        'observed': sum(1 for p in PARAM_LIST if p['source'] == 'observed'),
        'public': sum(1 for p in PARAM_LIST if p['source'] == 'public'),
        'assumed': sum(1 for p in PARAM_LIST if p['source'] == 'assumed')
    },
    'params': PARAM_LIST
}
json.dump(out, open(PARAMS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('params: %d (observed %d / public %d / assumed %d)' % (
    out['count'], out['stats']['observed'], out['stats']['public'], out['stats']['assumed']))
