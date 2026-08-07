import { defineStore } from 'pinia'

const KEY = 'agri_theme'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    dark: localStorage.getItem(KEY) === 'dark',
  }),
  actions: {
    apply() {
      document.documentElement.classList.toggle('dark', this.dark)
      // Element Plus 深色开关
      document.documentElement.classList.toggle('el-dark', this.dark)
    },
    toggle() {
      this.dark = !this.dark
      localStorage.setItem(KEY, this.dark ? 'dark' : 'light')
      this.apply()
    },
  },
})