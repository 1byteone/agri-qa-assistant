<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="login-head">
        <h1>智慧农业管理系统</h1>
        <p>Smart Agriculture Management Platform · v2</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent>
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入账号"
            :prefix-icon="'User'"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            :prefix-icon="'Lock'"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          @click="onSubmit"
        >
          登 录
        </el-button>
      </el-form>

      <!-- 默认管理员提示：点击一键填充 -->
      <div class="default-tip" @click="fillDefault">
        <el-icon><InfoFilled /></el-icon>
        <span>
          默认管理员：<b>admin</b> / <b>admin123</b>
          <span class="fill-hint">（点击一键填充）</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function fillDefault() {
  form.username = 'admin'
  form.password = 'admin123'
}

async function onSubmit() {
  console.log('[login-debug] onSubmit fired, formRef=', !!formRef.value,
    'username=', form.username, 'password=', form.password)
  try {
    const ok = await formRef.value.validate()
    console.log('[login-debug] validate ok=', !!ok)
  } catch (e) {
    console.log('[login-debug] validate FAILED', e)
    return
  }
  if (!form.username.trim() || !form.password) return
  loading.value = true
  try {
    console.log('[login-debug] calling login api')
    await auth.login(form.username.trim(), form.password)
    console.log('[login-debug] login success')
    ElMessage.success('登录成功，欢迎回来')
    router.push(route.query.redirect || '/cockpit')
  } catch (e) {
    console.log('[login-debug] login error', e.response?.status, e.message)
    // 401 由登录页提示；429 等其他错误由拦截器统一提示
    if (e.response?.status === 401) ElMessage.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a1122 0%, #10264d 45%, #0d3b66 100%);
  position: relative;
  overflow: hidden;
}
.login-wrap::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(79, 157, 255, 0.25), transparent 65%);
  top: -160px;
  right: -120px;
}
.login-wrap::after {
  content: '';
  position: absolute;
  width: 480px;
  height: 480px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(34, 176, 125, 0.18), transparent 65%);
  bottom: -140px;
  left: -100px;
}
.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  padding: 40px 36px 28px;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 14px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.45);
}
.login-head { text-align: center; margin-bottom: 26px; }
.login-head h1 { margin: 0 0 6px; font-size: 22px; color: #10264d; }
.login-head p { margin: 0; font-size: 12px; color: #6b7f99; letter-spacing: 1px; }
.login-btn { width: 100%; margin-top: 4px; }
.default-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 18px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f0f5ff;
  color: #5a7db8;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.default-tip:hover { background: #e3edff; }
.fill-hint { opacity: 0.7; }
</style>