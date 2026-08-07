<template>
  <router-view />
</template>

<script setup>
import { useThemeStore } from './stores/theme'

// 启动即应用已保存主题（深/浅）
const theme = useThemeStore()
theme.apply()
</script>