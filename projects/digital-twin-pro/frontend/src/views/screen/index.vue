<template>
  <div class="screen-page">
    <iframe
      ref="iframeRef"
      class="screen-frame"
      src="/screen/digital_twin_pro.html"
      width="100%"
      height="100%"
      border="0"
      frameborder="0"
      allowfullscreen
      @load="onIframeLoad"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const iframeRef = ref(null)

// iframe 加载完成后通知大屏（大屏若不监听 postMessage 则无害）
function onIframeLoad() {
  const win = iframeRef.value?.contentWindow
  if (win) {
    try {
      win.postMessage({ type: 'AGRI_SCREEN_READY' }, window.location.origin)
    } catch (e) {
      // 忽略跨域安全限制（同源场景下不会触发）
    }
  }
}
</script>

<style scoped>
.screen-page {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #050d1f;
}
.screen-frame {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}
</style>