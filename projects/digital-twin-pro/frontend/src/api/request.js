import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截：统一带 Bearer token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('agri_admin_token')
  if (token) config.headers.Authorization = 'Bearer ' + token
  return config
})

// 响应拦截：统一错误提示；401 清 token 跳登录
request.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    if (status === 401) {
      localStorage.removeItem('agri_admin_token')
      if (router.currentRoute.value.path !== '/login') {
        ElMessage.error('登录已失效，请重新登录')
        router.push('/login')
      }
    } else {
      const msg = typeof detail === 'string' ? detail
        : (error.response?.data?.message || error.message || '请求失败')
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  },
)

export default request