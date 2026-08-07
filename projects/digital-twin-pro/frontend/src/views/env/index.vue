<template>
  <div class="v2-page">
    <!-- 5 类传感器实时卡片 -->
    <el-row :gutter="16">
      <el-col v-for="m in metrics" :key="m.key" :xs="12" :sm="8" :md="4.8">
        <div class="v2-card metric-card" :class="{ warn: m.status !== 'normal' }">
          <div class="metric-top">
            <span class="metric-label">{{ m.label }}</span>
            <el-tag size="small" :type="m.status === 'normal' ? 'success' : 'danger'">
              {{ m.status === 'normal' ? '正常' : '超限' }}
            </el-tag>
          </div>
          <div class="metric-value">{{ m.value ?? '—' }}<span class="metric-unit">{{ m.unit }}</span></div>
          <div class="metric-sub">{{ m.device || '暂无数据' }} · {{ m.ts || '' }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mt16">
      <!-- 实时曲线 -->
      <el-col :md="15" :xs="24">
        <div class="v2-card">
          <div class="card-title">
            实时监测曲线（每 3 秒刷新）
            <el-tag size="small" class="live-tag" type="success">LIVE</el-tag>
          </div>
          <div ref="chartRef" class="chart-box"></div>
        </div>
      </el-col>
      <!-- 告警列表 -->
      <el-col :md="9" :xs="24">
        <div class="v2-card">
          <div class="card-title">告警列表（未确认 {{ unacked.length }} 条）</div>
          <div v-if="unacked.length" class="alert-list">
            <div v-for="a in unacked" :key="a.id" class="alert-item" :class="'lv-' + a.level">
              <div class="alert-head">
                <el-tag size="small" :type="a.level === 'critical' ? 'danger' : 'warning'" effect="dark">
                  {{ a.level === 'critical' ? '严重' : '警告' }}
                </el-tag>
                <span class="alert-type">{{ a.type }}</span>
                <span class="alert-time">{{ a.ts }}</span>
              </div>
              <div class="alert-msg">{{ a.message }}</div>
              <el-button size="small" type="primary" plain @click="ack(a)">确认</el-button>
            </div>
          </div>
          <el-empty v-else description="暂无未确认告警" :image-size="60" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '../../api/request'

const chartRef = ref(null)
let chart = null
let timer = null

const metrics = reactive([
  { key: 'temp', label: '温度', unit: '°C', value: null, device: '', ts: '', status: 'normal' },
  { key: 'humidity', label: '湿度', unit: '%', value: null, device: '', ts: '', status: 'normal' },
  { key: 'ph', label: '土壤PH', unit: '', value: null, device: '', ts: '', status: 'normal' },
  { key: 'light', label: '光照', unit: 'lux', value: null, device: '', ts: '', status: 'normal' },
  { key: 'moisture', label: '土壤墒情', unit: '%', value: null, device: '', ts: '', status: 'normal' },
])

const unacked = ref([])
const seriesCache = reactive({ temp: [], humidity: [], ph: [], light: [], moisture: [] })

function checkStatus(key, v) {
  if (key === 'temp') return v > 35 ? 'warn' : 'normal'
  if (key === 'humidity') return v < 40 ? 'warn' : 'normal'
  if (key === 'ph') return v < 5.5 || v > 7.5 ? 'warn' : 'normal'
  if (key === 'light') return v > 75000 ? 'warn' : 'normal'
  if (key === 'moisture') return v < 22 ? 'warn' : 'normal'
  return 'normal'
}

async function poll() {
  try {
    const [latest, history, alerts] = await Promise.all([
      request.get('/sensors/latest'),
      request.get('/sensors/history', { params: { limit: 150 } }),
      request.get('/alerts', { params: { ack: 0, limit: 50 } }),
    ])

    // 实时卡片：按类型取最新一条
    const latestByType = {}
    latest.data.items.forEach((it) => {
      const cur = latestByType[it.type]
      if (!cur || it.ts > cur.ts) latestByType[it.type] = it
    })
    metrics.forEach((m) => {
      const it = latestByType[m.key]
      if (it) {
        m.value = it.value
        m.device = it.device_name || it.device_code
        m.ts = (it.ts || '').slice(11)
        m.status = checkStatus(m.key, it.value)
      }
    })

    // 曲线：按类型分组，追加时间点
    const groups = {}
    history.data.items.forEach((it) => {
      if (!groups[it.type]) groups[it.type] = []
      groups[it.type].push({ t: (it.ts || '').slice(11, 19), v: it.value })
    })
    Object.keys(seriesCache).forEach((k) => {
      const g = groups[k] || []
      seriesCache[k].push(...g)
      if (seriesCache[k].length > 60) seriesCache[k].splice(0, seriesCache[k].length - 60)
    })
    renderChart()

    // 告警
    unacked.value = alerts.data.items || []
  } catch (e) {
    // 轮询失败静默，下次重试
  }
}

const LINE_COLORS = { temp: '#f08a5d', humidity: '#4f9dff', ph: '#a78bfa', light: '#fbbf24', moisture: '#34d399' }

function renderChart() {
  if (!chart) chart = echarts.init(chartRef.value)
  const maxLen = Math.max(...Object.values(seriesCache).map((a) => a.length), 1)
  const xData = []
  for (let i = 0; i < maxLen; i++) xData.push(i)
  const series = Object.keys(seriesCache).map((k) => ({
    name: metrics.find((m) => m.key === k)?.label || k,
    type: 'line',
    smooth: true,
    showSymbol: false,
    data: seriesCache[k].map((p) => p.v),
    lineStyle: { width: 2, color: LINE_COLORS[k] },
    itemStyle: { color: LINE_COLORS[k] },
  }))
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: series.map((s) => s.name), top: 0 },
    grid: { left: 50, right: 16, top: 36, bottom: 24 },
    xAxis: { type: 'category', data: xData, show: false },
    yAxis: { type: 'value', scale: true },
    series,
  }, true)
}

async function ack(a) {
  await request.put(`/alerts/${a.id}/ack`)
  ElMessage.success('告警已确认')
  unacked.value = unacked.value.filter((x) => x.id !== a.id)
}

onMounted(() => {
  poll()
  timer = setInterval(poll, 3000)
  window.addEventListener('resize', onResize)
})

function onResize() {
  chart?.resize()
}

onBeforeUnmount(() => {
  clearInterval(timer)
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<style scoped>
.mt16 { margin-top: 16px; }
.card-title { font-weight: 600; margin-bottom: 12px; }
.live-tag { margin-left: 8px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.metric-card { text-align: center; border-left: 4px solid #22b07d; }
.metric-card.warn { border-left-color: #e5534b; }
.metric-top { display: flex; justify-content: space-between; align-items: center; }
.metric-label { font-size: 13px; color: var(--text-sub); }
.metric-value { font-size: 26px; font-weight: 700; margin: 10px 0 4px; font-variant-numeric: tabular-nums; }
.metric-unit { font-size: 12px; color: var(--text-sub); margin-left: 2px; }
.metric-sub { font-size: 11px; color: var(--text-sub); }
.alert-list { display: flex; flex-direction: column; gap: 10px; max-height: 380px; overflow-y: auto; }
.alert-item {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.alert-item.lv-critical { border-left: 4px solid #e5534b; }
.alert-item.lv-warning { border-left: 4px solid #f0a020; }
.alert-head { display: flex; align-items: center; gap: 8px; }
.alert-type { font-weight: 600; font-size: 13px; }
.alert-time { margin-left: auto; font-size: 11px; color: var(--text-sub); }
.alert-msg { font-size: 12px; color: var(--text-sub); }
</style>