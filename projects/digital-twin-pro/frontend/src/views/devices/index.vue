<template>
  <div class="v2-page">
    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :xs="12" :sm="6">
        <div class="kpi-card kpi-grad-blue">
          <div class="kpi-label">设备总数</div>
          <div class="kpi-value">{{ stats.total }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="kpi-card kpi-grad-green">
          <div class="kpi-label">在线</div>
          <div class="kpi-value">{{ stats.online }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="kpi-card kpi-grad-cyan">
          <div class="kpi-label">离线</div>
          <div class="kpi-value">{{ stats.offline }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="kpi-card kpi-grad-red">
          <div class="kpi-label">故障</div>
          <div class="kpi-value">{{ stats.fault }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mt16">
      <el-col :md="5" :xs="24">
        <div class="v2-card center-card">
          <div class="card-title">在线率</div>
          <el-progress type="dashboard" :percentage="stats.online_rate" :color="rateColor" :width="150" />
          <div class="rate-tip">统计周期：实时</div>
        </div>
      </el-col>
      <el-col :md="19" :xs="24">
        <div class="v2-card">
          <div class="toolbar">
            <el-select v-model="filters.status" placeholder="状态" clearable style="width: 110px">
              <el-option label="在线" value="online" />
              <el-option label="离线" value="offline" />
              <el-option label="故障" value="fault" />
            </el-select>
            <el-select v-model="filters.type" placeholder="类型" clearable style="width: 140px">
              <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
            <el-button type="primary" :icon="'Search'" @click="load(1)">查询</el-button>
            <div class="spacer" />
            <el-button type="primary" plain :icon="'Plus'" @click="openAdd">新增设备</el-button>
          </div>

          <el-table :data="rows" v-loading="loading" border stripe>
            <el-table-column prop="code" label="设备编号" width="130" />
            <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small" :type="typeTag(row.type)">{{ typeLabel(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="province" label="省份" width="90" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="statusTag(row.status)" effect="light">
                  <span class="dot" :class="'dot-' + row.status" />{{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="在线率" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.online_rate" :stroke-width="8" :color="rateColor" style="width: 90px" />
              </template>
            </el-table-column>
            <el-table-column prop="last_seen" label="最后数据时间" width="170">
              <template #default="{ row }">{{ row.last_seen || '—' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status !== 'online'"
                  link type="success" @click="command(row, 'on')"
                >启动</el-button>
                <el-button
                  v-else link type="warning" @click="command(row, 'off')"
                >停机</el-button>
                <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button link type="danger" @click="remove(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pager"
            layout="total, prev, pager, next"
            :total="total"
            v-model:current-page="filters.page"
            :page-size="filters.page_size"
            @current-change="load()"
          />
        </div>
      </el-col>
    </el-row>

    <!-- 新增/编辑 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑设备' : '新增设备'" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="设备编号" prop="code">
          <el-input v-model="form.code" :disabled="dialog.isEdit" placeholder="如 SOIL-SD-02" />
        </el-form-item>
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" style="width: 200px">
            <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="省份" prop="province">
          <el-select v-model="form.province" filterable allow-create style="width: 200px">
            <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" style="width: 160px">
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="故障" value="fault" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const stats = reactive({ total: 0, online: 0, offline: 0, fault: 0, online_rate: 0 })
const provinces = ref([])
const formRef = ref(null)

const typeOptions = [
  { value: 'soil', label: '土壤传感器' },
  { value: 'weather', label: '气象站' },
  { value: 'irrigation', label: '灌溉控制器' },
  { value: 'camera', label: '摄像头' },
]
const filters = reactive({ status: null, type: null, page: 1, page_size: 10 })
const dialog = reactive({ visible: false, isEdit: false })
const form = reactive({ id: null, code: '', name: '', type: 'soil', province: '', status: 'online' })
const rules = {
  code: [{ required: true, message: '请输入设备编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
}

const typeLabel = (t) => typeOptions.find((o) => o.value === t)?.label || t
const typeTag = (t) => ({ soil: 'success', weather: 'warning', irrigation: 'primary', camera: 'info' }[t] || 'info')
const statusLabel = (s) => ({ online: '在线', offline: '离线', fault: '故障' }[s] || s)
const statusTag = (s) => ({ online: 'success', offline: 'info', fault: 'danger' }[s] || 'info')
const rateColor = (p) => (p >= 80 ? '#22b07d' : p >= 50 ? '#f0a020' : '#e5534b')

async function loadStats() {
  const { data } = await request.get('/devices/stats')
  Object.assign(stats, data)
}

async function load(page) {
  if (page) filters.page = page
  loading.value = true
  try {
    const params = { page: filters.page, page_size: filters.page_size }
    if (filters.status) params.status = filters.status
    if (filters.type) params.type = filters.type
    const { data } = await request.get('/devices', { params })
    rows.value = data.items || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

function openAdd() {
  Object.assign(form, { id: null, code: '', name: '', type: 'soil', province: '', status: 'online' })
  dialog.isEdit = false
  dialog.visible = true
}

function openEdit(row) {
  Object.assign(form, { id: row.id, code: row.code, name: row.name, type: row.type, province: row.province, status: row.status })
  dialog.isEdit = true
  dialog.visible = true
}

async function submit() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { code: form.code, name: form.name, type: form.type, province: form.province, status: form.status }
    if (dialog.isEdit) {
      await request.put('/devices/' + form.id, { name: form.name, type: form.type, province: form.province, status: form.status })
    } else {
      await request.post('/devices', payload)
    }
    ElMessage.success('保存成功')
    dialog.visible = false
    load()
    loadStats()
  } catch (e) {
    // 拦截器已提示
  } finally {
    saving.value = false
  }
}

async function command(row, action) {
  const { data } = await request.post(`/devices/${row.id}/command`, { action })
  ElMessage.success(data.status === 'online' ? '设备已启动' : '设备已停机')
  load()
  loadStats()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除设备「${row.name}」？`, '提示', { type: 'warning' })
  await request.delete('/devices/' + row.id)
  ElMessage.success('删除成功')
  load()
  loadStats()
}

onMounted(async () => {
  const { data } = await request.get('/meta/dimensions')
  provinces.value = (data.regions || []).map((r) => r.province).filter((p) => p && p !== '全国')
  load()
  loadStats()
})
</script>

<style scoped>
.mt16 { margin-top: 16px; }
.card-title { font-weight: 600; margin-bottom: 12px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.spacer { flex: 1; }
.pager { margin-top: 12px; justify-content: flex-end; }
.center-card { text-align: center; }
.center-card .card-title { text-align: left; }
.rate-tip { margin-top: 10px; font-size: 12px; color: var(--text-sub); }
.dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  margin-right: 5px;
}
.dot-online { background: #22b07d; }
.dot-offline { background: #9aa8bd; }
.dot-fault { background: #e5534b; }
</style>