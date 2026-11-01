<script setup lang="ts">
import { computed } from 'vue'
import { Database, FlaskConical, CircleHelp, Map, ShieldCheck, FileText, PlugZap } from 'lucide-vue-next'
import { dataMeta } from '@/composables/useData'
import { probeNote, probing } from '@/composables/useDataSource'
import { useAppStore } from '@/stores/app'
import { SITES } from '@/data/sites'
import stats from '@/data/statistics.json'
import { useReveal } from '@/composables/useReveal'

const store = useAppStore()
const statistics: any[] = (stats as any).records ?? []

const tagLegend = [
  { cls: 'tag--public', name: '公开资料', desc: '来自学生手册、学校官网或公开报道，标注来源编号与适用时期。' },
  { cls: 'tag--sim', name: '演示假设', desc: '容量、到件量、取件需求、处理能力等，全部为模拟数值，不代表真实业务量。' },
  { cls: 'tag--unknown', name: '待核实', desc: '面积、货架数、库容、柜台营业时间等未取得公开数据的字段，显示「待核实」而非 0。' }
]

const sources = [
  { id: 'S01', name: '学生手册 · 物流服务', url: 'https://www.cumtlive.com/Life/Service/Logistics.html', use: '站点位置、服务方式、常态营业时间' },
  { id: 'S02', name: '学生手册 · 矿大地图快速上手', url: 'https://www.cumtlive.com/Freshman/矿大地图快速上手.html', use: '校园方位与地名' },
  { id: 'S03', name: '总务部 · 2025 南湖菜鸟驿站报道', url: 'https://zwb.cumt.edu.cn/info/1029/7982.htm', use: '日均件量量级（限 2025-04 报道期）' },
  { id: 'S04', name: '总务部 · 2022 无人快递超市改建', url: 'https://zwb.cumt.edu.cn/info/1029/5811.htm', use: '无人站设立背景' },
  { id: 'S07', name: '总务部 · 2025 暑期后勤服务', url: 'https://zwb.cumt.edu.cn/info/1027/8255.htm', use: '暑期件量参考（仅作量级参考）' },
  { id: 'S09', name: '信息化部门 · 校园地图入口', url: 'https://nic.cumt.edu.cn/fwzn2/xydt.htm', use: '校园地图资源入口' },
  { id: 'S11', name: '基建处 · 历史规划平面图', url: 'https://jjc.cumt.edu.cn/info/1054/1312.htm', use: '校园平面参考' }
]

const osmSources = [
  { name: '学生手册《校园物流服务点分布图》', url: '', use: '默认底图；四个红点即站点位置，离线可用' },
  { name: 'Esri ArcGIS World Imagery', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer', use: '卫星影像底图（在线瓦片，仅演示用）' },
  { name: 'OpenStreetMap（ODbL-1.0）', url: 'https://www.openstreetmap.org/copyright', use: '只用于核对站点方位与校区范围，不再作为底图渲染' }
]

const modelRows = computed(() => Object.entries(dataMeta.value.formulas))

useReveal(".panel")
</script>

<template>
  <div class="ab">
    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><PlugZap :size="15" /> 当前数据来源</h2>
        <span class="panel__hint">
          <span class="tag" :class="store.dataMode === 'api' ? 'tag--public' : 'tag--sim'">
            {{ store.dataMode === 'api' ? '后端接口' : '内置样例' }}
          </span>
        </span>
      </div>
      <div class="panel__body">
        <p class="dsrc">{{ probing ? '正在检测…' : probeNote }}</p>
        <p class="note">
          页面启动时先渲染内置样例，再异步探测 <code>/api/scenarios</code>；探测成功就整包换成接口数据，
          失败则静默沿用样例。两种来源的字段结构完全一致，切换不影响任何页面逻辑。
          现在展示的所有到件量、取件需求、处理能力都是<b>演示假设值</b>，不是学校真实业务数据。
        </p>
      </div>
    </section>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><ShieldCheck :size="15" /> 三类标签，任何页面都不混用</h2>
      </div>
      <div class="panel__body legend">
        <div v-for="l in tagLegend" :key="l.name" class="legend__row">
          <span class="tag" :class="l.cls">{{ l.name }}</span>
          <p>{{ l.desc }}</p>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><Database :size="15" /> 公开资料来源</h2>
        <span class="panel__hint">完整清单见 data/source_catalog.json</span>
      </div>
      <div class="panel__body">
        <table class="tbl">
          <thead>
            <tr><th>编号</th><th>来源</th><th>用途</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in sources" :key="s.id">
              <td class="num">{{ s.id }}</td>
              <td><a :href="s.url" target="_blank" rel="noopener noreferrer">{{ s.name }}</a></td>
              <td>{{ s.use }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><Map :size="15" /> 地图数据来源</h2>
        <span class="panel__hint">矢量底图离线可用，卫星层需联网</span>
      </div>
      <div class="panel__body">
        <table class="tbl">
          <thead><tr><th>来源</th><th>用途</th></tr></thead>
          <tbody>
            <tr v-for="s in osmSources" :key="s.name">
              <td><a :href="s.url" target="_blank" rel="noopener noreferrer">{{ s.name }}</a></td>
              <td>{{ s.use }}</td>
            </tr>
          </tbody>
        </table>
        <p class="note">
          地图只剩两种底图：<b>手册原图</b>（默认，离线可用，四个红点就是站点真值）与
          <b>卫星影像</b>（Esri 在线瓦片，需联网）。原先那套 OSM 矢量底图已经去掉——
          它在宿舍区几乎是空白，看不出楼，反而误导。
        </p>
        <p class="note">
          手册原图是网页地图截图，和卫星影像不是同一套投影，像素坐标不能直接当经纬度用，
          所以顶栏放了「校准站点位置」：把原图拖到与卫星影像重合（或直接在地图上按顺序点四个位置），
          坐标由程序反算并记住，之后图标就会落在红点上。站点经纬度仍属<b>演示近似</b>，不是测绘成果。
        </p>
      </div>
    </section>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><FileText :size="15" /> 有时期限制的公开统计</h2>
        <span class="panel__hint">不得外推为常态</span>
      </div>
      <div class="panel__body">
        <table class="tbl">
          <thead><tr><th>编号</th><th>指标</th><th>数值</th><th>适用时期</th><th>禁止用途</th></tr></thead>
          <tbody>
            <tr v-for="s in statistics" :key="s.id">
              <td class="num">{{ s.id }}</td>
              <td>{{ s.metric }}</td>
              <td class="num">{{ s.operator === '>' ? '>' : '' }}{{ s.value }}{{ s.unit === '%' ? '%' : '' }} <span class="unit">{{ s.unit }}</span></td>
              <td>{{ s.period }}</td>
              <td class="forbid">{{ s.forbidden_use }}</td>
            </tr>
          </tbody>
        </table>
        <p class="warn-box">{{ (stats as any).warning }}</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><FlaskConical :size="15" /> 仿真模型假设</h2>
        <span class="panel__hint">生成于 {{ dataMeta.generatedAt }}</span>
      </div>
      <div class="panel__body">
        <ul class="model">
          <li v-for="[k, v] in modelRows" :key="k"><code>{{ v }}</code></li>
        </ul>
        <p class="note">
          时间桶 {{ dataMeta.bucketMinutes }} 分钟，07:00—23:30 共 33 桶；桃苑 08:30—18:30 只占其中 20 桶。
          同一时段处理完的包裹可当段取走；未满足的取件需求不结转。
        </p>
        <p class="warn-box">{{ dataMeta.warning }}</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title"><CircleHelp :size="15" /> 明确不做的内容</h2>
      </div>
      <div class="panel__body">
        <ul class="donts">
          <li>不做寒暑假、法定节假日等特殊时段场景（按用户指示裁剪）</li>
          <li>不做登录、权限、多租户</li>
          <li>不做真实运单、扫码、支付</li>
          <li>不做三维地球、路径规划与真实导航</li>
          <li>不虚构没有公开证据的站点（如竹苑独立驿站、杏苑站点）</li>
          <li>不把近似经纬度当实测坐标，不把像素坐标当经纬度</li>
        </ul>
      </div>
    </section>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title">四站速查</h2>
      </div>
      <div class="panel__body">
        <table class="tbl">
          <thead><tr><th>站点</th><th>角色</th><th>位置</th><th>常态营业</th><th>近似经纬度</th></tr></thead>
          <tbody>
            <tr v-for="s in SITES" :key="s.id">
              <td><i class="dot" :style="{ background: s.color }" />{{ s.name }}</td>
              <td>{{ s.roleLabel }}</td>
              <td>{{ s.locationText }}</td>
              <td class="num">{{ s.hours.open }}—{{ s.hours.close }}</td>
              <td class="num">{{ store.sitePos(s.id).lat.toFixed(4) }}, {{ store.sitePos(s.id).lng.toFixed(4) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.ab { display: grid; gap: var(--sp-5); }

.legend { display: grid; gap: var(--sp-3); }
.dsrc { font-size: var(--fs-sm); color: var(--fg-0); line-height: var(--lh-loose); }
.legend__row { display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: var(--sp-3); align-items: start; }
.legend__row p { font-size: var(--fs-sm); color: var(--fg-1); line-height: var(--lh-loose); }

.tbl { font-size: var(--fs-sm); }
.tbl th {
  text-align: left; font-size: var(--fs-xs); font-weight: 600; color: var(--fg-2);
  padding: var(--sp-2) var(--sp-3); border-bottom: 1px solid var(--line);
}
.tbl td { padding: var(--sp-3); border-bottom: 1px solid var(--line); color: var(--fg-1); vertical-align: top; }
.tbl tr:last-child td { border-bottom: none; }
.tbl a { color: var(--info-ink); text-decoration: underline; text-underline-offset: 2px; }
.tbl a:hover { color: var(--brand); }
.unit { color: var(--fg-2); font-size: var(--fs-xs); }
.forbid { color: var(--fg-2); font-size: var(--fs-xs); }
.dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: var(--sp-2); }

.note { font-size: var(--fs-xs); color: var(--fg-2); line-height: var(--lh-loose); margin-top: var(--sp-3); }
.note b { color: var(--fg-1); }

.model { display: grid; gap: var(--sp-2); }
.model code {
  font-family: 'JetBrains Mono', Consolas, ui-monospace, monospace;
  font-size: var(--fs-xs);
  color: var(--brand);
  background: var(--bg-2);
  padding: 3px var(--sp-3);
  border-radius: var(--r-sm);
  display: inline-block;
}

.warn-box {
  margin-top: var(--sp-3);
  padding: var(--sp-3);
  font-size: var(--fs-xs);
  color: var(--warn-ink);
  background: var(--warn-dim);
  border: 1px dashed rgb(232 163 61 / 0.35);
  border-radius: var(--r-md);
}

.donts { display: grid; gap: var(--sp-2); }
.donts li {
  font-size: var(--fs-sm); color: var(--fg-1);
  padding-left: var(--sp-4); position: relative; line-height: var(--lh-loose);
}
.donts li::before { content: '×'; position: absolute; left: 2px; color: var(--danger-ink); font-weight: 700; }

@media (max-width: 800px) {
  .legend__row { grid-template-columns: 1fr; }
}
</style>
