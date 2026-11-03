# -*- coding: utf-8 -*-
"""把桃苑实景照片的读数并进参数注册表与素材目录。"""
import json
import os

ROOT = r'D:\java大作业'
REG = os.path.join(ROOT, 'data', 'params', 'param_registry.json')
CAT = os.path.join(ROOT, 'data', 'source_catalog.json')
ASSETS = os.path.join(ROOT, 'data', 'assets_catalog.json')

# ---------- 1. 新增来源 S25 ----------
cat = json.load(open(CAT, encoding='utf-8'))
if not any(s['id'] == 'S25' for s in cat['sources']):
    cat['sources'].append({
        "id": "S25",
        "title": "桃苑物流服务中心内部实景照片（4 张）",
        "publisher": "用户本人拍摄",
        "source_type": "user_field_photo",
        "url": None,
        "published_date": "2026-11-03",
        "retrieved_at": "2026-11-03T00:00:00+00:00",
        "download_status": "local_copy",
        "local_path": "reference/taoyuan_interior/",
        "use_scope": "货架编号体系、取件码规则、层数、通道与分区；结构化为 reference/taoyuan_photo_evidence.json。仅用于本项目课程演示，对外发布需用户同意。"
    })
json.dump(cat, open(CAT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('sources', len(cat['sources']))

# ---------- 2. 参数注册表 ----------
reg = json.load(open(REG, encoding='utf-8'))
by_id = {p['id']: p for p in reg['params']}

def upsert(p):
    if p['id'] in by_id:
        by_id[p['id']].update(p)
    else:
        reg['params'].append(p)
        by_id[p['id']] = p

upsert(dict(
    id='P-CODE-FORMAT', group='C 储位', label='取件码结构',
    value='货架号(3位)-层号(1位)-序号(4位)', unit='格式', range=None,
    source='observed', source_ids=['S25', 'S20'],
    evidence='reference/taoyuan_photo_evidence.json#pickup_code_format',
    rationale='四张实景照片的每块货架号牌底部都印着“取件码规则”示例（108-3-2441、147-3-2441、41-1），'
              '格式统一为 货架号-层号-序号；S20 的公开报道只说到“前两位对货架与层”，本项以照片为准。',
    used_by=['取件码生成'], swap_hint='以驿站实际短信为准'))

upsert(dict(
    id='P-SHELF-SPEC', group='C 储位', label='货架外形与构造',
    value={'length_mm': 1500, 'depth_mm': 600, 'height_mm': 2000, 'type': '重型金属货架，红横梁+灰立柱+白层板'},
    unit='mm', range=[0.85, 1.15], source='observed', source_ids=['S25', 'S23'],
    evidence='reference/taoyuan_photo_evidence.json#shelf_construction',
    rationale='照片中为典型仓储货架，横梁红色、立柱灰色；高度与人的比例约 2 m，深度按标准 0.6 m；'
              '长度按号牌跨度与通道内可见货架段估 1.5 m。S23 的商品规格（1.8 m 长）作为同量级佐证。',
    used_by=['平面图模板', '储位分配'], swap_hint='以实测尺寸替换'))

upsert(dict(
    id='P-TIERS', group='C 储位', label='货架层数（含顶层）',
    value=4, unit='层', range=[3, 5], source='observed', source_ids=['S25'],
    evidence='reference/taoyuan_photo_evidence.json#tiers',
    rationale='货架端部层标可见 41-1、41-2、41-3，即单架至少 3 层；按 2 m 架高与常见层距推算为 4 层（含顶层）。',
    used_by=['平面图模板', '储位分配'], swap_hint='以正面照片确认'))

upsert(dict(
    id='P-SLOTS-PER-TIER', group='C 储位', label='每层储位数',
    value=12, unit='个', range=[8, 15], source='observed', source_ids=['S25'],
    evidence='reference/taoyuan_photo_evidence.json#derived_layout',
    rationale='照片中单层可见包裹 8—15 件（含平放叠放），取中值 12；'
              '与“一件一格”相比，实际是“一件一个位置”，小件可前后相邻放置。',
    used_by=['平面图模板', '储位分配'], swap_hint='以正面照片逐层清点'))

upsert(dict(
    id='P-RACK-COUNT', group='C 储位', label='主站货架总数',
    value=155, unit='架', range=[120, 180], source='observed', source_ids=['S25'],
    evidence='reference/taoyuan_photo_evidence.json#rack_numbering',
    rationale='四张照片的号牌覆盖 25—155 区间（25-29、30-34、36-41、47-53、71-77、78-84、85-91、92-98、'
              '103-107、108-114、147-154、155），编号连续，最小可见 155，故至少 155 架；'
              '1—24 与 115—146 未拍到，不代表不存在，因此区间取 120—180。',
    used_by=['平面图模板', '储位分配', '容量换算'], swap_hint='以全景照片或平面图确认后替换'))

upsert(dict(
    id='P-AISLE-WIDTH', group='C 储位', label='货架间通道宽度',
    value=1.3, unit='m', range=[1.1, 1.6], source='observed', source_ids=['S25'],
    evidence='reference/taoyuan_photo_evidence.json#aisle',
    rationale='照片中两人错身需侧身、手推车可单向通过，按人体宽度与货架比例估 1.3 m。',
    used_by=['平面图模板'], swap_hint='以实测替换'))

upsert(dict(
    id='P-SLOT-CAPACITY', group='C 储位', label='单储位容量',
    value=1, unit='件', range=[1, 2], source='observed', source_ids=['S25'],
    evidence='reference/taoyuan_photo_evidence.json#parcel_label',
    rationale='照片中每个位置放一件并贴 4 位序号标签，便于按码定位；小件偶有前后相邻两件。',
    used_by=['储位分配'], swap_hint='—'))

upsert(dict(
    id='P-PHYSICAL-SLOTS', group='C 储位', label='物理储位总数（推算）',
    value=7440, unit='个', range=[3840, 13500], source='observed', source_ids=['S25'],
    evidence='reference/taoyuan_photo_evidence.json#derived_layout',
    rationale='= 货架 155 × 层 4 × 每层 12。区间按 (120—180) × (3—5) × (8—15) 的四角组合给上下界。',
    used_by=['容量换算'], swap_hint='以实测替换'))

upsert(dict(
    id='P-KAPPA-I-SHARE', group='C 储位', label='待取区占物理储位的比例',
    value=0.32, unit='比例', range=[0.25, 0.45], source='assumed', source_ids=['S25'],
    evidence=None,
    rationale='宏观模型的待取上限 κ_i（桃苑 2372 件）除以物理储位 7440 得 0.319。'
              '物理解释：其余货架要留给分拣暂存、大件区与通道作业，不可能把货架塞满到顶，'
              '所以“运营上限”只有物理容量的三分之一左右。',
    used_by=['宏观层与实体层对齐'], swap_hint='拿到真实在架件数与货架数后重算'))

reg['stats'] = {
    'observed': sum(1 for p in reg['params'] if p['source'] == 'observed'),
    'public': sum(1 for p in reg['params'] if p['source'] == 'public'),
    'assumed': sum(1 for p in reg['params'] if p['source'] == 'assumed')
}
reg['count'] = len(reg['params'])
reg['generated_at'] = '2026-11-03'
reg['policy']['photo_evidence'] = '照片读数记为 observed，并在 evidence 字段指出结构化文件中的证据位置'
json.dump(reg, open(REG, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('params', reg['count'], reg['stats'])

# ---------- 3. 素材目录 ----------
assets = json.load(open(ASSETS, encoding='utf-8'))
have = {a['id'] for a in assets.get('assets', [])}
CH = [
    ('A12', '桃苑主站：顺丰服务台与 25—53 号货架', 'P1_sf_counter_and_racks25-53.jpg'),
    ('A13', '桃苑主站：108—114 号货架与自助取件导向牌', 'P2_rack108-114_aisle_and_sign.jpg'),
    ('A14', '桃苑主站：147—154 号货架号牌与空置备用架', 'P3_racks147-155_board_pair.jpg'),
    ('A15', '桃苑主站：71—107 号货架段与结构柱', 'P4_racks71-107_signs_and_column.jpg'),
]
for aid, title, fn in CH:
    if aid in have:
        continue
    assets.setdefault('assets', []).append({
        "id": aid,
        "title": title,
        "asset_type": "user_field_photo",
        "local_path": "reference/taoyuan_interior/" + fn,
        "source_ids": ["S25"],
        "license_status": "user_owned",
        "use_restriction": "用户本人拍摄；本项目课程演示与报告可用，对外公开需用户同意",
        "content_caveats": "手机广角拍摄，边缘有畸变；尺寸为目测估算，非实测"
    })
json.dump(assets, open(ASSETS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('assets', len(assets['assets']))
