<template>
  <div class="v2-page">
    <el-row :gutter="16">
      <!-- 左侧地图 -->
      <el-col :md="14" :xs="24">
        <div class="v2-card">
          <div class="card-title">
            农田健康地图
            <el-radio-group v-model="mapMode" size="small" style="margin-left: 12px">
              <el-radio-button value="province">按省着色</el-radio-button>
              <el-radio-button value="fields">地块标记</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="mapRef" class="chart-box map-box"></div>
        </div>
      </el-col>

      <!-- 右侧地块列表 -->
      <el-col :md="10" :xs="24">
        <div class="v2-card">
          <div class="card-title">
            地块列表（共 {{ fields.length }} 块）
            <div class="legend">
              <span class="lg lg-good">优</span>
              <span class="lg lg-normal">良</span>
              <span class="lg lg-bad">差</span>
            </div>
          </div>
          <el-table :data="fields" v-loading="loading" border stripe height="440">
            <el-table-column prop="name" label="地块名称" min-width="150" show-overflow-tooltip />
            <el-table-column prop="province" label="省份" width="80" />
            <el-table-column prop="area" label="面积(亩)" width="90" align="right">
              <template #default="{ row }">{{ fmt(row.area) }}</template>
            </el-table-column>
            <el-table-column prop="main_crop" label="主作物" width="90" show-overflow-tooltip />
            <el-table-column prop="health" label="健康" width="70" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="healthTag(row.health)" effect="dark">{{ row.health }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="owner" label="负责人" width="90" show-overflow-tooltip />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import request from '../../api/request'

const mapRef = ref(null)
const fields = ref([])
const loading = ref(false)
const mapMode = ref('province')
let chart = null
let geoJson = null

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
  return Number(n ?? 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}
function healthTag(h) {
  return { 优: 'success', 良: 'warning', 差: 'danger' }[h] || 'info'
}

// 从 GeoJSON 多边形粗略计算省中心点（演示用）
function centroidOf(feature) {
  const polys = feature.geometry.type === 'Polygon'
    ? [feature.geometry.coordinates]
    : feature.geometry.coordinates
  let best = null
  let bestArea = -1
  polys.forEach((rings) => {
    rings.forEach((ring) => {
      let x = 0; let y = 0; let a = 0
      for (let i = 0; i < ring.length - 1; i++) {
        const [x1, y1] = ring[i]; const [x2, y2] = ring[i + 1]
        const cross = x1 * y2 - x2 * y1
        a += cross
        x += (x1 + x2) * cross
        y += (y1 + y2) * cross
      }
      a /= 2
      if (a > bestArea) {
        bestArea = a
        best = [x / (6 * a), y / (6 * a)]
      }
    })
  })
  return best
}

async function loadFields() {
  loading.value = true
  try {
    const { data } = await request.get('/fields')
    fields.value = data.items || []
  } finally {
    loading.value = false
  }
}

async function renderMap() {
  if (!chart) chart = echarts.init(mapRef.value)
  if (!geoJson) {
    const resp = await fetch('/vendor/china.json')
    geoJson = await resp.json()
  }
  echarts.registerMap('china', geoJson)

  // 省份健康评分：优=2 良=1 差=0（无地块省份不显示）
  const score = {}
  const markers = []
  const nameFull = new Map(geoJson.features.map((f) => [f.properties.name, f]))
  fields.value.forEach((f) => {
    const full = provinceFull(f.province)
    const feat = nameFull.get(full)
    if (feat) {
      const pt = centroidOf(feat)
      if (pt) markers.push({ name: f.name, value: [...pt, f.area], health: f.health, field: f })
    }
    if (!score[full]) score[full] = []
    score[full].push(f.health === '优' ? 2 : f.health === '差' ? 0 : 1)
  })

  const mapData = Object.entries(score).map(([full, arr]) => ({
    name: full,
    value: arr.reduce((a, b) => a + b, 0) / arr.length,
  }))

  const fieldScatter = markers.map((m) => ({
    name: m.field.name,
    value: [m.value[0], m.value[1]],
    field: m.field,
  }))

  const baseOption = {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        if (p.seriesType === 'effectScatter' && p.data?.field) {
          const f = p.data.field
          return `${f.name}<br/>省份：${f.province}｜面积：${fmt(f.area)} 亩<br/>主作物：${f.main_crop}｜健康：${f.health}`
        }
        if (p.data && p.value !== undefined && p.seriesType === 'map') {
          const v = p.value
          const label = v >= 1.5 ? '优' : v >= 0.5 ? '良' : '差'
          return `${p.name}<br/>健康等级：${label}`
        }
        return p.name
      },
    },
    geo: {
      map: 'china',
      roam: true,
      zoom: 1.2,
      itemStyle: { areaColor: '#e8eef7', borderColor: '#8fa3bd' },
      emphasis: { itemStyle: { areaColor: '#cfe3ff' } },
    },
  }

  const provinceSeries = {
    series: [{
      type: 'map',
      map: 'china',
      roam: true,
      zoom: 1.2,
      label: { show: false },
      itemStyle: { borderColor: '#8fa3bd' },
      emphasis: { label: { show: true } },
      data: mapData,
      visualMap: {
        type: 'piecewise',
        pieces: [
          { gte: 1.5, label: '优', color: '#34d399' },
          { min: 0.5, lt: 1.5, label: '良', color: '#fbbf24' },
          { lt: 0.5, label: '差', color: '#f87171' },
        ],
        left: 10,
        bottom: 10,
      },
    }],
  }

  const fieldSeries = {
    series: [{
      type: 'map',
      map: 'china',
      roam: true,
      zoom: 1.2,
      label: { show: false },
      itemStyle: { areaColor: '#e8eef7', borderColor: '#8fa3bd' },
      emphasis: { label: { show: true } },
      data: [],
    }, {
      type: 'effectScatter',
      coordinateSystem: 'geo',
      zlevel: 2,
      rippleEffect: { brushType: 'stroke' },
      label: { show: true, position: 'right', formatter: '{b}', fontSize: 10 },
      symbolSize: 12,
      itemStyle: { color: (params) => ({ 优: '#34d399', 良: '#fbbf24', 差: '#f87171' })[params.data?.field?.health] || '#4f9dff' },
      data: fieldScatter,
    }],
  }

  chart.setOption({ ...baseOption, ...(mapMode.value === 'province' ? provinceSeries : fieldSeries) }, true)
}

watch(mapMode, () => renderMap())

onMounted(async () => {
  await loadFields()
  renderMap()
  window.addEventListener('resize', () => chart?.resize())
})

onBeforeUnmount(() => {
  chart?.dispose()
})
</script>

<style scoped>
.card-title {
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.map-box { height: 500px; }
.legend { display: flex; gap: 8px; }
.lg {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  color: #fff;
}
.lg-good { background: #34d399; }
.lg-normal { background: #fbbf24; }
.lg-bad { background: #f87171; }
</style>