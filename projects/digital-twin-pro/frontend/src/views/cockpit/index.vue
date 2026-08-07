<template>
  <div class="v2-page">
    <!-- KPI 卡片 -->
    <el-row :gutter="16">
      <el-col v-for="k in kpis" :key="k.label" :xs="12" :sm="8" :md="4">
        <div class="kpi-card" :class="k.cls">
          <div class="kpi-label">{{ k.label }}</div>
          <div class="kpi-value">{{ k.value }}</div>
          <div class="kpi-sub">{{ k.sub }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 中部：对比柱状图 + Top10 排名 -->
    <el-row :gutter="16" class="mt16">
      <el-col :md="16">
        <div class="v2-card">
          <div class="card-title">各省产量对比（2023 vs 2024，吨）</div>
          <div ref="barRef" class="chart-box"></div>
        </div>
      </el-col>
      <el-col :md="8">
        <div class="v2-card">
          <div class="card-title">省份产量 Top10（{{ lastYear }}）</div>
          <div v-if="top10.length" class="rank-list">
            <div v-for="(item, i) in top10" :key="item.name" class="rank-item">
              <span class="rank-no" :class="{ top: i < 3 }">{{ i + 1 }}</span>
              <span class="rank-name">{{ item.name }}</span>
              <div class="rank-bar">
                <div class="rank-bar-inner" :style="{ width: pct(item.production) + '%' }"></div>
              </div>
              <span class="rank-val">{{ fmt(item.production) }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="60" />
        </div>
      </el-col>
    </el-row>

    <!-- 底部：中国地图（本地 GeoJSON） -->
    <el-row :gutter="16" class="mt16">
      <el-col :span="24">
        <div class="v2-card">
          <div class="card-title">全国产量分布（{{ lastYear }}）</div>
          <div ref="mapRef" class="chart-box map-box"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import request from '../../api/request'

const barRef = ref(null)
const mapRef = ref(null)
let barChart = null
let mapChart = null

const kpis = reactive([])
const top10 = ref([])
const lastYear = ref('')

// 省份简称 → 全称（对齐 GeoJSON 的 name 字段）
const FULL_SPECIAL = {
  内蒙古: '内蒙古自治区', 广西: '广西壮族自治区', 西藏: '西藏自治区',
  宁夏: '宁夏回族自治区', 新疆: '新疆维吾尔自治区', 北京: '北京市',
  天津: '天津市', 上海: '上海市', 重庆: '重庆市', 香港: '香港特别行政区',
  澳门: '澳门特别行政区',
}
function provinceFull(short) {
  if (FULL_SPECIAL[short]) return FULL_SPECIAL[short]
  if (/[省市自治区]$/.test(short)) return short
  return short + '省'
}

function fmt(n) {
  if (n === null || n === undefined) return '-'
  return Number(n).toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}

function pct(v) {
  const max = Math.max(...top10.value.map((x) => x.production), 1)
  return Math.max(4, (v / max) * 100)
}

function animateValue(el, target, suffix = '') {
  const dur = 900
  const start = performance.now()
  function step(now) {
    const t = Math.min(1, (now - start) / dur)
    const val = Math.round(target * (1 - Math.pow(1 - t, 3)))
    el.textContent = val.toLocaleString('zh-CN') + suffix
    if (t < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

async function load() {
  const [dash, meta, devStats, alerts] = await Promise.all([
    request.get('/dashboard'),
    request.get('/meta/dimensions'),
    request.get('/devices/stats'),
    request.get('/alerts', { params: { ack: 0, limit: 200 } }),
  ])
  const dashData = dash.data
  const years = dashData.years || []
  lastYear.value = String(dashData.province.length ? Math.max(...dashData.province.map((p) => p.year)) : (years[years.length - 1] || ''))
  const cur = dashData.kpi?.[lastYear.value] || {}
  const prev = dashData.yoy?.base_year ? dashData.kpi?.[String(dashData.yoy.base_year)] : null
  const yoyProd = dashData.yoy?.production_change_pct ?? null
  const yoyArea = dashData.yoy?.area_change_pct ?? null

  const today = new Date().toISOString().slice(0, 10)
  const todayAlerts = alerts.data.items.filter((a) => (a.ts || '').startsWith(today)).length

  const kpiDefs = [
    { label: '总产量（吨）', value: cur.total_production || 0, sub: yoyProd === null ? '—' : (yoyProd >= 0 ? '同比 +' + yoyProd + '%' : '同比 ' + yoyProd + '%'), cls: 'kpi-grad-blue' },
    { label: '总面积（亩）', value: cur.total_area || 0, sub: yoyArea === null ? '—' : (yoyArea >= 0 ? '同比 +' + yoyArea + '%' : '同比 ' + yoyArea + '%'), cls: 'kpi-grad-green' },
    { label: '作物种类数', value: meta.data.counts?.dim_crop || 0, sub: lastYear.value + ' 年口径', cls: 'kpi-grad-purple' },
    { label: '覆盖省份数', value: dashData.province ? new Set(dashData.province.map((p) => p.province)).size : 0, sub: lastYear.value + ' 年', cls: 'kpi-grad-cyan' },
    { label: '设备在线率', value: devStats.data.online_rate || 0, sub: devStats.data.online + '/' + devStats.data.total + ' 台在线', cls: 'kpi-grad-orange' },
    { label: '今日告警', value: todayAlerts, sub: '未确认告警', cls: 'kpi-grad-red' },
  ]
  kpis.splice(0, kpis.length, ...kpiDefs.map((d) => ({ ...d })))

  // 中部：各省产量对比柱状图
  const byYear = { 2023: {}, 2024: {} }
  dashData.province.forEach((p) => {
    if (!byYear[p.year]) byYear[p.year] = {}
    byYear[p.year][p.province] = p.production
  })
  const prov2024 = Object.entries(byYear[2024] || {}).sort((a, b) => b[1] - a[1]).slice(0, 15)
  const names = prov2024.map(([n]) => n)
  const d2023 = names.map((n) => byYear[2023]?.[n] ?? 0)
  const d2024 = names.map((n) => byYear[2024]?.[n] ?? 0)
  renderBar(names, d2023, d2024)

  // Top10 排名
  top10.value = (dashData.rankings?.by_region || []).slice(0, 10)

  // 地图
  renderMap(dashData.mapData || [])
}

function renderBar(names, d2023, d2024) {
  if (!barChart) barChart = echarts.init(barRef.value)
  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['2023', '2024'], top: 0 },
    grid: { left: 60, right: 16, top: 36, bottom: 40 },
    xAxis: { type: 'category', data: names, axisLabel: { rotate: 40, fontSize: 10 } },
    yAxis: { type: 'value', name: '吨' },
    series: [
      { name: '2023', type: 'bar', data: d2023, itemStyle: { color: '#8fa3bd' }, barMaxWidth: 16 },
      { name: '2024', type: 'bar', data: d2024, itemStyle: { color: '#2f7cf6' }, barMaxWidth: 16 },
    ],
  })
}

async function renderMap(mapData) {
  if (!mapChart) mapChart = echarts.init(mapRef.value)
  let geo = null
  try {
    const resp = await fetch('/vendor/china.json')
    geo = await resp.json()
  } catch (e) {
    mapChart.clear()
    mapChart.setOption({
      title: { text: '地图数据不可用', left: 'center', top: 'middle', textStyle: { fontSize: 14, color: '#8fa3bd' } },
    })
    return
  }
  echarts.registerMap('china', geo)
  const mapped = mapData.map((d) => ({
    name: provinceFull(d.name),
    value: d.production,
    short: d.name,
  }))
  mapChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        if (!p.data) return p.name
        return `${p.data.short || p.name}<br/>产量：${fmt(p.value)} 吨`
      },
    },
    visualMap: {
      min: 0,
      max: Math.max(...mapped.map((m) => m.value), 1),
      left: 10,
      bottom: 10,
      text: ['高', '低'],
      calculable: true,
      inRange: { color: ['#d8e6f8', '#4f9dff', '#1d4e89'] },
    },
    series: [{
      type: 'map',
      map: 'china',
      roam: true,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 10 } },
      data: mapped,
    }],
  })
}

function resize() {
  barChart?.resize()
  mapChart?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', resize)
  // KPI 数字滚动动画
  setTimeout(() => {
    document.querySelectorAll('.kpi-value').forEach((el, i) => {
      const raw = kpis[i]?.value
      animateValue(el, Number(raw) || 0, typeof raw === 'number' && kpis[i].label.includes('率') ? '%' : '')
    })
  }, 300)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  barChart?.dispose()
  mapChart?.dispose()
})
</script>

<style scoped>
.mt16 { margin-top: 16px; }
.card-title { font-weight: 600; margin-bottom: 12px; color: var(--text-main); }
.map-box { height: 420px; }
.rank-list { display: flex; flex-direction: column; gap: 10px; }
.rank-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.rank-no {
  width: 20px; height: 20px; border-radius: 4px;
  background: var(--chart-grid); color: var(--text-sub);
  display: inline-flex; align-items: center; justify-content: center; font-size: 11px;
  flex-shrink: 0;
}
.rank-no.top { background: #f0a020; color: #fff; }
.rank-name { width: 56px; flex-shrink: 0; }
.rank-bar { flex: 1; height: 10px; background: var(--chart-grid); border-radius: 5px; overflow: hidden; }
.rank-bar-inner { height: 100%; background: linear-gradient(90deg, #2f7cf6, #4f9dff); border-radius: 5px; transition: width 0.6s; }
.rank-val { width: 70px; text-align: right; font-variant-numeric: tabular-nums; color: var(--text-sub); }
</style>