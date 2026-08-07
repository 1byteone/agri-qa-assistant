<template>
  <div class="v2-page data-page">
    <el-row :gutter="16">
      <!-- 左侧：作物分类树 -->
      <el-col :md="5" :xs="24">
        <div class="v2-card tree-card">
          <div class="card-title">作物分类</div>
          <el-tree
            :data="treeData"
            node-key="key"
            highlight-current
            :props="{ label: 'label', children: 'children' }"
            :expand-on-click-node="false"
            @node-click="onTreeClick"
          >
            <template #default="{ data }">
              <span class="tree-node">
                <el-icon v-if="!data.children"><Cherry /></el-icon>
                <el-icon v-else><FolderOpened /></el-icon>
                <span>{{ data.label }}</span>
              </span>
            </template>
          </el-tree>
        </div>
      </el-col>

      <!-- 中部：数据表格 -->
      <el-col :md="19" :xs="24">
        <div class="v2-card">
          <!-- 工具栏 -->
          <div class="toolbar">
            <el-select v-model="filters.year" placeholder="年份" clearable style="width: 100px">
              <el-option v-for="y in years" :key="y" :label="y + '年'" :value="y" />
            </el-select>
            <el-select v-model="filters.region" placeholder="省份" clearable filterable style="width: 130px">
              <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
            </el-select>
            <el-select v-model="filters.indicator" placeholder="指标" clearable style="width: 110px">
              <el-option label="产量" value="产量" />
              <el-option label="面积" value="面积" />
            </el-select>
            <el-button type="primary" :icon="'Search'" @click="load(1)">查询</el-button>
            <div class="spacer" />
            <el-button type="primary" plain :icon="'Plus'" @click="openAdd">新增</el-button>
            <el-button type="danger" plain :icon="'Delete'" :disabled="!selected.length" @click="batchDelete">
              批量删除
            </el-button>
            <el-button :icon="'Upload'" @click="importRef?.click()">导入CSV</el-button>
            <el-button :icon="'Download'" @click="exportCsv">导出CSV</el-button>
            <input ref="importRef" type="file" accept=".csv" style="display:none" @change="onImport" />
          </div>

          <el-table
            :data="rows"
            v-loading="loading"
            border
            stripe
            @selection-change="(s) => (selected = s)"
            @sort-change="onSort"
          >
            <el-table-column type="selection" width="42" />
            <el-table-column prop="year" label="年份" width="80" sortable="custom" />
            <el-table-column prop="province" label="省份" width="110" />
            <el-table-column prop="crop" label="作物" min-width="120" show-overflow-tooltip />
            <el-table-column prop="crop_category" label="分类" width="110">
              <template #default="{ row }">
                <el-tag size="small" :type="tagType(row.crop_category)">{{ row.crop_category }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="indicator" label="指标" width="80" />
            <el-table-column prop="value" label="数值" width="120" sortable="custom" align="right">
              <template #default="{ row }">{{ fmt(row.value) }} {{ row.unit }}</template>
            </el-table-column>
            <el-table-column prop="source" label="来源" min-width="100" show-overflow-tooltip />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button link type="danger" @click="remove(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pager"
            layout="total, sizes, prev, pager, next"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            v-model:current-page="filters.page"
            v-model:page-size="filters.page_size"
            @current-change="load()"
            @size-change="load(1)"
          />
        </div>
      </el-col>
    </el-row>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑记录' : '新增记录'" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="年份" prop="year">
          <el-input-number v-model="form.year" :min="1990" :max="2099" style="width: 160px" />
        </el-form-item>
        <el-form-item label="省份" prop="province">
          <el-select v-model="form.province" filterable allow-create default-first-option style="width: 220px">
            <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="作物" prop="crop">
          <el-input v-model="form.crop" placeholder="如：水稻" />
        </el-form-item>
        <el-form-item label="分类" prop="crop_category">
          <el-select v-model="form.crop_category" style="width: 220px">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="指标" prop="indicator">
          <el-select v-model="form.indicator" style="width: 160px">
            <el-option label="产量" value="产量" />
            <el-option label="面积" value="面积" />
          </el-select>
        </el-form-item>
        <el-form-item :label="form.indicator === '面积' ? '面积（亩）' : '产量（吨）'" prop="value">
          <el-input-number v-model="form.value" :min="0" :precision="2" style="width: 220px" />
        </el-form-item>
        <el-form-item label="来源" prop="source">
          <el-input v-model="form.source" placeholder="数据来源（可选）" />
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
const selected = ref([])
const years = ref([])
const provinces = ref([])
const categories = ['粮食作物', '经济作物', '其他作物']
const treeData = ref([])
const importRef = ref(null)
const formRef = ref(null)

const filters = reactive({ year: null, region: null, indicator: null, crop: null, page: 1, page_size: 20, sort: 'year', order: 'asc' })

const dialog = reactive({ visible: false, isEdit: false })
const form = reactive({ fact_id: null, year: 2024, province: '', crop: '', crop_category: '粮食作物', indicator: '产量', value: 0, source: '' })

const rules = {
  province: [{ required: true, message: '请选择省份', trigger: 'change' }],
  crop: [{ required: true, message: '请输入作物', trigger: 'blur' }],
  value: [{ required: true, message: '请输入数值' }],
}

function fmt(n) {
  return Number(n ?? 0).toLocaleString('zh-CN', { maximumFractionDigits: 1 })
}
function tagType(cat) {
  if (cat === '粮食作物') return 'warning'
  if (cat === '经济作物') return 'success'
  return 'info'
}

async function loadMeta() {
  const { data } = await request.get('/meta/dimensions')
  years.value = data.years || []
  provinces.value = (data.regions || []).map((r) => r.province).filter((p) => p && p !== '全国')
  // 分类树
  const map = {}
  ;(data.crops || []).forEach((c) => {
    const cat = c.category || '其他作物'
    if (!map[cat]) map[cat] = { label: cat, key: 'cat:' + cat, children: [] }
    map[cat].children.push({ label: c.name, key: 'crop:' + c.name })
  })
  treeData.value = Object.values(map).map((node) => ({
    ...node,
    children: node.children.length ? node.children : undefined,
  }))
}

async function load(page) {
  if (page) filters.page = page
  loading.value = true
  try {
    const params = {
      page: filters.page,
      page_size: filters.page_size,
      sort: filters.sort,
      order: filters.order,
    }
    if (filters.year) params.year = filters.year
    if (filters.region) params.region = filters.region
    if (filters.indicator) params.indicator = filters.indicator
    if (filters.crop) params.crop = filters.crop
    const { data } = await request.get('/records', { params })
    rows.value = data.items || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

function onSort({ prop, order }) {
  filters.sort = prop || 'year'
  filters.order = order === 'ascending' ? 'asc' : 'desc'
  load(1)
}

function onTreeClick(node) {
  filters.crop = node.key.startsWith('crop:') ? node.label : null
  load(1)
}

function openAdd() {
  Object.assign(form, { fact_id: null, year: 2024, province: '', crop: '', crop_category: '粮食作物', indicator: '产量', value: 0, source: '' })
  dialog.isEdit = false
  dialog.visible = true
}

function openEdit(row) {
  Object.assign(form, {
    fact_id: row.fact_id, year: row.year, province: row.province, crop: row.crop,
    crop_category: row.crop_category || '粮食作物', indicator: row.indicator,
    value: row.value, source: row.source || '',
  })
  dialog.isEdit = true
  dialog.visible = true
}

async function submit() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = {
      year: form.year, province: form.province, crop: form.crop,
      crop_category: form.crop_category, indicator: form.indicator,
      value: form.value, source: form.source || '', unit: '',
    }
    if (dialog.isEdit) {
      await request.put('/records/' + form.fact_id, payload)
    } else {
      await request.post('/records', payload)
    }
    ElMessage.success('保存成功')
    dialog.visible = false
    load()
  } catch (e) {
    // 拦截器已提示（409 重复 / 401 需登录）
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除 ${row.province}·${row.crop}·${row.year} 记录？`, '提示', { type: 'warning' })
  await request.delete('/records/' + row.fact_id)
  ElMessage.success('删除成功')
  load()
}

async function batchDelete() {
  await ElMessageBox.confirm(`确认删除选中的 ${selected.value.length} 条记录？`, '提示', { type: 'warning' })
  await Promise.all(selected.value.map((r) => request.delete('/records/' + r.fact_id)))
  ElMessage.success('批量删除成功')
  load()
}

function exportCsv() {
  const p = new URLSearchParams()
  if (filters.year) p.set('year', filters.year)
  if (filters.region) p.set('region', filters.region)
  if (filters.indicator) p.set('indicator', filters.indicator)
  if (filters.crop) p.set('crop', filters.crop)
  window.open('/api/export/csv?' + p.toString(), '_blank')
}

async function onImport(e) {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    const { data } = await request.post('/import/csv', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success(`导入完成：新增 ${data.inserted_rows} 行，更新 ${data.updated_rows} 行，失败 ${data.failed_rows} 行`)
    load()
  } catch (err) {
    // 拦截器已提示
  } finally {
    e.target.value = ''
  }
}

onMounted(async () => {
  await loadMeta()
  load()
})
</script>

<style scoped>
.tree-card { min-height: 480px; }
.card-title { font-weight: 600; margin-bottom: 12px; }
.tree-node { display: inline-flex; align-items: center; gap: 4px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.spacer { flex: 1; }
.pager { margin-top: 12px; justify-content: flex-end; }
</style>