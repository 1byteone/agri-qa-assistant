import { defineStore } from 'pinia'
import request from '../api/request'

const TOKEN_KEY = 'agri_admin_token'
const USER_KEY = 'agri_admin_user'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    username: localStorage.getItem(USER_KEY) || '',
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
  },
  actions: {
    async login(username, password) {
      // 账号密码登录：成功返回现有管理 token
      const { data } = await request.post('/auth/login', { username, password })
      this.token = data.token
      this.username = data.username || username
      localStorage.setItem(TOKEN_KEY, this.token)
      localStorage.setItem(USER_KEY, this.username)
      return data
    },
    async verify(token) {
      // 兼容旧机制：手动校验 token 有效性
      const { data } = await request.post('/auth/verify', null, {
        headers: { Authorization: 'Bearer ' + token },
      })
      if (!data.valid) throw new Error('Token 无效')
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
      return true
    },
    logout() {
      this.token = ''
      this.username = ''
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})