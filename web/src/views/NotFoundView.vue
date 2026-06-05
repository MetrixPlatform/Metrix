<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <h1>404</h1>
      <p>页面不存在，{{ seconds }} 秒后返回主页</p>
      <n-button type="primary" @click="goHome">返回主页</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";
import { useRouter } from "vue-router";
import { NButton } from "naive-ui";

const router = useRouter();
const seconds = ref(5);
let timer = window.setInterval(() => {
  seconds.value -= 1;
  if (seconds.value <= 0) {
    goHome();
  }
}, 1000);

onBeforeUnmount(() => {
  clearTimer();
});

function clearTimer() {
  window.clearInterval(timer);
  timer = 0;
}

function goHome() {
  clearTimer();
  void router.replace("/");
}
</script>
