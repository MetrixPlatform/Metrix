<template>
  <div class="brand-mark">
    <img class="brand-logo" :src="logoUrl" :alt="APP_NAME" />
  </div>
</template>

<script setup lang="ts">
import { APP_NAME } from "../config/app";

const logoUrl = "/favicon.svg";
</script>
