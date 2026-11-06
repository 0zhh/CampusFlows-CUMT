# 驿链 CampusFlow · UI 升级方案（液态玻璃方向）

> 版本 v1.0 · 2026-11-06
> 目标：把"一眼 AI 模板"的卡片墙，改成有材质、有层次、有品牌记忆点的调度台；
> 液态玻璃只用在"光学玻璃该出现的地方"，不用它包住正文。

---

## 一、先说诊断：为什么会显得"AI 生成"

我把现在的实现逐条对照了一遍，问题不在配色，而在**结构太整齐、材质太单一**：

| # | 症状 | 现在的代码证据 |
|---|---|---|
| 1 | **卡片墙** | 总览 6 个 KPI 一字排开，宽高完全一致，只有数字不同 |
| 2 | **一种盒子走天下** | `.panel` 全局只有一套：`bg-1` + 1px `--line` + `r-lg` + `shadow-1`，所有面板共用 |
| 3 | **没有材质层次** | 画布 `bg-0` 与面板 `bg-1` 只差一档亮度，没有"浮起来"的感觉 |
| 4 | **字体没有性格** | `system-ui + 微软雅黑` 兜底栈，标题与正文只差字号，没有字重/字距的品牌处理 |
| 5 | **图标同质** | 全是 Lucide 默认 13—16px 线性图标，圆角端点、描边一致 |
| 6 | **图表默认皮肤** | ECharts 网格线 + 默认 tooltip，和页面其余部分两套语言 |
| 7 | **没有纹理** | 纯色背景，暗色下发灰、亮色下发白，缺"空气感" |
| 8 | **动效只有淡入** | 面板统一 0.3s 淡入，没有层级位移、没有惯性 |

结论：**不是换成玻璃就高级了**。玻璃只是"表面"，先要有层次和品牌语言，玻璃才站得住。

---

## 二、方向：三层材质 + 一个品牌记忆点

### 2.1 三层抬高（elevation）

| 层 | 用途 | 材质 |
|---|---|---|
| **画布 Canvas** | 页面底色 | 深炭黑 + 两处径向光晕（左上冷、右下暖）+ 2 % 颗粒噪点 |
| **石板 Slab** | 内容面板、表格、图表 | 半透明石板：上沿 1px 高光 + 底部投影 + 极轻微渐变，**不做模糊** |
| **玻璃 Glass** | 顶栏、底部调度坞、抽屉、弹层 | 模糊 22px + 饱和度 180 % + 锥形高光边 + 内顶光，**只在这些"漂浮层"上** |

比例控制：玻璃面积 ≤ 视口 15 %。内容区一律石板，保证长文与表格的可读性。

### 2.2 品牌记忆点

现在整个站只有"暖金"一个识别物。建议加两个：

1. **站名牌式标题**：页面标题左侧加一条 3px 的琥珀色竖杠 + 小号等宽编号（P1/P2…），像站台编号牌
2. **地图既是背景也是主角**：总览把地图做成"底片层"，面板半透明浮在上面（只有这一屏允许玻璃叠地图）

### 2.3 配色微调（不是推翻）


| token | 现在 | 建议 | 理由 |
|---|---|---|---|
| `--bg-0` | `#080b10` | `#070a0e` + 光晕 | 纯黑发死，加两处径向光晕才有"空气" |
| `--bg-1` | `#10151c` | 半透明 `rgb(255 255 255 / .05)` | 石板要能透出底色 |
| `--brand` | `#e8a33d` | 保留 | 暖金是驿站的记忆点，别换 |
| 新增 `--glass-tint` | — | `rgb(232 163 61 / .06)` | 玻璃带一点点品牌色，才不像系统面板 |

---

## 三、液态玻璃：技术配方与实测结论

### 3.1 我踩到的一个坑（重要）

第一版方向稿给玻璃层直接挂了 SVG 位移滤镜：

```css
.glass { filter: url(#liquid-lens); }   /* feTurbulence + feDisplacementMap */
```

渲染出来整块顶栏**扭曲、文字跟着变形**（截图右边那版就是）。原因：`filter` 作用在元素**渲染结果**上，
文字也在里面；而且 `backdrop-filter` 与 SVG filter 叠加时行为各浏览器不一致。

**结论：位移折射只适合做装饰层**（图标透镜、按钮高光），**不能挂在文字容器上**。
生产版本的"液态感"靠**光**（模糊、折射感的锥形高光边、内阴影），不靠"变形"。

### 3.2 生产配方（四层叠加）

```css
.glass {
  /* ① 底：半透明渐变，让背景透上来但保留对比度 */
  background: linear-gradient(180deg, rgb(255 255 255 / .10), rgb(255 255 255 / .04));
  /* ② 模糊 + 提饱和：玻璃的"磨砂"感 */
  backdrop-filter: blur(22px) saturate(180%);
  border-radius: 22px;
  /* ③ 内顶光 + 底影：制造厚度 */
  box-shadow:
    0 1px 0 rgb(255 255 255 / .28) inset,
    0 -1px 0 rgb(255 255 255 / .06) inset,
    0 24px 60px rgb(0 0 0 / .55);
}
/* ④ 锥形高光边：只在 1px 描边上出现，模拟折射 */
.glass::before {
  content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1px;
  background: conic-gradient(from 140deg,
    rgb(255 255 255 / .85), rgb(255 255 255 / .10) 22%,
    rgb(232 163 61 / .55) 38%, rgb(255 255 255 / .08) 55%,
    rgb(62 201 167 / .45) 72%, rgb(255 255 255 / .75));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
  pointer-events: none;
}
```

### 3.3 降级与可达性（必须做）

| 场景 | 处理 |
|---|---|
| `prefers-reduced-transparency` | 玻璃退化为不透明 `--bg-1`，去掉 blur |
| `prefers-reduced-motion` | 关掉高光扫过、悬浮位移 |
| 玻璃上的文字 | 必须有 scrim（`rgb(0 0 0 / .35)`）或实底，正文对比度 ≥ 4.5:1 |
| 低端机 / 无 `backdrop-filter` | ``supports` 检测，不支持就走石板样式 |
| 滚动容器内 | 禁止大面积 blur（每帧重绘，掉帧），只在固定层用 |

### 3.4 组件封装建议

```vue
<!-- GlassSurface.vue -->
<template>
  <component :is="as" class="glass" :class="[`glass--${level}`, { 'glass--static': !motion }]"
             :style="{ '--glass-tint': tint }">
    <slot />
  </component>
</template>
<script setup lang="ts">
withDefaults(defineProps<{
  as?: string
  level?: 'nav' | 'dock' | 'sheet'   // 控制模糊半径与圆角
  tint?: string                        // 品牌色渗入比例
  motion?: boolean                     // 是否允许高光扫过
}>(), { as: 'div', level: 'nav', tint: 'rgb(232 163 61 / .06)', motion: true })
</script>
```

---

## 四、组件级改造清单

| 组件 | 现在 | 改成 |
|---|---|---|
| 顶栏 | 纯色 + 1px 底边 | **玻璃**：模糊 + 锥形边；导航用胶囊高亮；右侧数据源 chip 改成"信号灯"（脉冲点） |
| KPI 卡 | 6 张同构卡片 | 主卡（1 张，大号 44px 数字 + 迷你折线）+ 5 张小卡（28px）；主卡用琥珀色渐变描边 |
| 面板 | 统一 `.panel` | 石板材质；标题加"站台编号"竖杠；面板间距改为 20/28 两档，形成节奏 |
| 地图坞 | 无 | **底部悬浮玻璃坞**：入口切换（北门/东门）+ 播放 + 批次时间，胶囊按钮 |
| 抽屉 | 右侧滑出白板 | 玻璃 sheet（模糊 + 左边缘高光），内容仍用石板 |
| 表格 | 斑马纹 | 去掉斑马纹，改行悬停高亮 + 首列固定 + 数字右对齐等宽 |
| 图表 | ECharts 默认 | 统一到"发光细线 + 渐变面积"；网格只剩水平线，透明度 6 % |
| 按钮/标签 | 直角小圆角 | 胶囊化；主按钮加内顶光；危险操作加 1px 琥珀边而不是整块红 |
| 图标 | Lucide 默认 | 保留 Lucide，但统一 `stroke-width: 1.75`、14px 网格、与文字基线对齐 |
| 空态/加载 | 无 | 骨架屏用石板色扫光；空态配地图线稿插画 |

---

## 五、分期与验收

| 阶段 | 内容 | 验收 | 预估 |
|---|---|---|---|
| **S1 基础层** | 新 token（三层材质、光晕、颗粒）、`GlassSurface`、顶栏玻璃、底部坞 | 截图对比明显不同；对比度扫描通过；60fps | 1.5 天 |
| **S2 内容层** | KPI 主次分级、面板石板化、表格与图表统一 | `audit.mjs` 0 裁剪；`interact` 全绿 | 2 天 |
| **S3 记忆点** | 站台编号标题、地图底片化、动效（高光扫过、批次推进） | 录屏观感检查；reduced-motion 正常 | 1.5 天 |

**统一验收口径**：

1. `node scripts/audit.mjs` 六页 × 三档宽度：0 裁剪、0 重叠
2. 文字对比度 ≥ 4.5:1（玻璃层单独测）
3. 首屏 JS 增量 < 15 KB（纯 CSS 实现，不引第三方库）
4. `prefers-reduced-motion` / `reduced-transparency` 下功能与可读性不降级

---

## 六、可以借鉴的开源项目

| 项目 | 形态 | 能借什么 |
|---|---|---|
| [awesome-liquid-glass](https://github.com/carolhsiaoo/awesome-liquid-glass) | 资源索引 | 官方 WWDC 视频、HIG 文档、Figma 组件、各家实现的总目录 |
| [shuding/liquid-glass](https://github.com/shuding/liquid-glass) | 纯 JS + SVG 滤镜 | 折射的实现思路（`feDisplacementMap` + 位移贴图），适合做装饰层 |
| [Muggleee/liquid-glass-vue](https://github.com/Muggleee/liquid-glass-vue) | **Vue + WebGL** | 和本项目同栈，可参考它的着色器写法；但 WebGL 成本高，只在大屏演示可选 |
| [liquid-glass-react](https://github.com/huangj17/liquid-glass-react) | React 组件 | API 设计（level / tint / motion）可以直接照搬成 Vue 版 |
| [lucasromerodb/liquid-glass-effect-macos](https://github.com/lucasromerodb/liquid-glass-effect-macos) | 纯 CSS + SVG | 纯 CSS 的降级写法，适合我们"不引依赖"的目标 |

> 结论：**不引入第三方运行时**。用纯 CSS 实现 3.2 的四层配方（约 40 行），
> 需要折射装饰时再抄 shuding 的滤镜参数，做成一个可选的 `<GlassLens>` 小组件。

---

## 七、风险

| 风险 | 影响 | 对策 |
|---|---|---|
| 大面积 blur 掉帧 | 滚动卡顿 | 玻璃只用于固定层；滚动容器内不用；`transform: translateZ(0)` 谨慎 |
| 玻璃上文字对比不足 | 可读性/可达性 | 强制 scrim；自动化对比度扫描 |
| 截图/测试不稳 | E2E 抖动 | 玻璃层给测试留 `data-glass` 标记，截图前可关闭动效 |
| 过度设计 | 反而更"AI" | 玻璃面积上限 15 %，内容区坚持石板 |

---

## 八、方向稿

- 可交互预览：`docs/ui/glass-mock.html`（浏览器直接打开，无依赖）
- 静帧：`docs/ui/方向稿-液态玻璃.png`

方向稿里已经落地的：光晕画布 + 颗粒、玻璃顶栏（锥形高光边）、石板 KPI、底部玻璃调度坞、胶囊入口切换。
它只是**方向验证**，不是最终实现——正式改的时候会按第四节逐组件替换。
