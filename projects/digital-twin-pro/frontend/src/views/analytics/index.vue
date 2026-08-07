<template>
  <div class="v2-page">
    <el-row :gutter="16">
      <el-col :md="14" :xs="24">
        <div class="v2-card">
          <div class="card-title">省级产量对比（吨）</div>
          <div ref="barRef" class="chart-box"></div>
        </div>
      </el-col>
      <el-col :md="10" :xs="24">
        <div class="v2-card">
          <div class="card-title">作物结构（分类占比）</div>
          <div ref="pieRef" class="chart-box"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mt16">
      <el-col :md="10" :xs="24">
        <div class="v2-card">
          <div class="card-title">Top 作物产量排名（{{ selectedYear }}）</div>
          <div ref="rankRef" class="chart-box"></div>
        </div>
      </el-col>
      <el-col :md="14" :xs="24">
        <div class="v2-card">
          <div class="card-title">
            <span>省份 × 作物明细（{{ selectedYear }}）</span>
            <span class="title-right">
              <el-select v-model="selectedProvince" size="small" style="width: 120px" @change="loadDetail">
                <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
              </el-select>
              <el-button size="small" :icon="'Download'" @click="exportCsv">导出CSV</el-button>
            </span>
          </div>
          <div class="detail-summary">
            总产量 {{ fmt(detail.total_production) }} 吨 ｜ 总面积 {{ fmt(detail.total_area) }} 亩 ｜
            主栽作物：{{ detail.main_crop || '—' }} ｜ 作物 {{ detail.crop_count }} 种
          </div>
          <el-table :data="detail.crops" v-loading="detailLoading" border stripe height="300">
            <el-table-column prop="name" label="作物" min-width="110" />
            <el-table-column prop="category" label="分类" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="catTag(row.category)">{{ row.category }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="production" label="产量(吨)" width="110" align="right">
              <template #default="{ row }">{{ fmt(row.production) }}</template>
            </el-table-column>
            <el-table-column prop="production_pct" label="占比%" width="90" align="right">
              <template #default="{ row }">{{ row.production_pct }}%</template>
            </el-table-column>
            <el-table-column prop="area" label="面积(亩)" width="110" align="right">
              <template #default="{ row }">{{ fmt(row.area) }}</template>
            </el-table-column>
            <el-table-column prop="unit_production" label="单产(吨/亩)" width="100" align="right" />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '../../api/request'

const barRef = ref(null)
const pieRef = ref(null)
const rankRef = ref(null)
let barChart = null
let pieChart = null
let rankChart = null

const years = ref([])
const selectedYear = ref('')
const provinces = ref([])
const selectedProvince = ref('')
const detail = ref({ total_production: 0, total_area: 0, main_crop: null, crop_count: 0, crops: [] })
const detailLoading = ref(false)

const CAT_COLORS = { 粮食作物: '#f59e0b', 经济作物: '#10b981', 其他作物: '#8b5cf6' }

function fmt(n) {
  return Number(n ?? 0).toLocaleString('zh-CN', { maximumFractionDigits: 1 })
}
function catTag(c) {
  return { 粮食: 'warning', 经济作物: 'success', 其他: 'info' }[c] || 'info'
}

async function loadOverview() {
  const { data } = await request.get('/dashboard')
  years.value = data.years || []
  const provincesArr = data.province || []
  selectedYear.value = String(provincesArr.length ? Math.max(...provincesArr.map((p) => p.year)) : (years.value[years.value.length - 1] || ''))
  provinces.value = [...new Set(provincesArr.map((p) => p.province))]
  if (!selectedProvince.value && provinces.value.length) {
    selectedProvince.value = provinces.value[0]
  }

  // 省级对比
  const byYear = {}
  provincesArr.forEach((p) => {
    if (!byYear[p.year]) byYear[p.year] = {}
    byYear[p.year][p.province] = p.production
  })
  const entries = Object.entries(byYear[selectedYear.value] || {}).sort((a, b) => b[1] - a[1]).slice(0, 12)
  const names = entries.map(([n]) => n)
  barChart = barChart || echarts.init(barRef.value)
  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 60, right: 16, top: 20, bottom: 46 },
    xAxis: { type: 'category', data: names, axisLabel: { rotate: 40, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: entries.map(([, v]) => v),
      barMaxWidth: 22,
      itemStyle: { borderRadius: [4, 4, 0, 0], color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: '#4f9dff' }, { offset: 1, color: '#1d6fe0' }]) },
    }],
  }, true)

  // 作物结构饼图
  const cats = data.categories?.[selectedYear.value] || []
  pieChart = pieChart || echarts.init(pieRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}：{c} 吨（{d}%）' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '68%'],
      center: ['50%', '44%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{d}%' },
      data: cats.map((c) => ({ name: c.name, value: c.production, itemStyle: { color: CAT_COLORS[c.name] || c.color } })),
    }],
  }, true)

  // Top 作物排名条形图
  const crops = (data.production_by_crop?.[selectedYear.value] || []).slice(0, 10).reverse()
  rankChart = rankChart || echarts.init(rankRef.value)
  rankChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 70, right: 60, top: 10, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: crops.map((c) => c.name) },
    series: [{
      type: 'bar',
      data: crops.map((c) => c.production),
      barMaxWidth: 14,
      label: { show: true, position: 'right', formatter: (p) => fmt(p.value) },
      itemStyle: { borderRadius: [0, 4, 4, 0], color: (p) => CAT_COLORS[crops[p.dataIndex]?.category] || '#2f7cf6' },
    }],
  }, true)

  loadDetail()
}

async function loadDetail() {
  if (!selectedProvince.value) return
  detailLoading.value = true
  try {
    const { data } = await request.get(`/analytics/province/${encodeURIComponent(selectedProvince.value)}`, {
      params: { year: selectedYear.value },
    })
    detail.value = data
  } catch (e) {
    detail.value = { total_production: 0, total_area: 0, main_crop: null, crop_count: 0, crops: [] }
  } finally {
    detailLoading.value = false
  }
}

function exportCsv() {
  if (!detail.value.crops.length) {
    ElMessage.warning('暂无明细数据可导出')
    return
  }
  const head = '省份,作物,分类,产量(吨),占比(%),面积(亩),单产(吨/亩)'
  const lines = detail.value.crops.map((c) =>
    [selectedProvince.value, c.name, c.category, c.production, c.production_pct, c.area, c.unit_production].join(','))
  const csv = '\ufeff' + [head, ...lines].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${selectedProvince.value}_${selectedYear.value}_明细.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function onResize() {
  barChart?.resize()
  pieChart?.resize()
  rankChart?.resize()
}

onMounted(() => {
  loadOverview()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  barChart?.dispose()
  pieChart?.dispose()
  rankChart?.dispose()
})
</script>

<style scoped>
.mt16 { margin-top: 16px; }
.card-title {
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.title-right { display: flex; align-items: center; gap: 8px; }
.detail-summary { font-size: 12px; color: var(--text-sub); margin-bottom: 10px; }
</style>