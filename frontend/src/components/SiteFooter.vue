<script setup lang="ts">
const year = new Date().getFullYear()
</script>

<template>
  <footer class="foot">
    <div class="foot__inner">
      <p>
        <strong>驿链 CampusFlow</strong> · 中国矿业大学南湖校区校园物流管理系统 · 课程演示原型
      </p>
      <p class="foot__meta">
        底图 © OpenStreetMap contributors（ODbL-1.0） · 站点位置为按公开资料近似定位，非测绘成果 ·
        本站所有业务数值均为演示假设
      </p>
      <p class="foot__meta">© {{ year }} · 仅用于课程作业演示，不代表学校实际运营安排</p>
    </div>
  </footer>
</template>

<style scoped>
.foot {
  border-top: 1px solid var(--line);
  background: var(--bg-1);
}
.foot__inner {
  max-width: var(--max-w);
  margin: 0 auto;
  padding: var(--sp-5);
  display: grid;
  gap: var(--sp-2);
  font-size: var(--fs-xs);
  color: var(--fg-2);
}
.foot__meta { line-height: var(--lh-loose); }
</style>
