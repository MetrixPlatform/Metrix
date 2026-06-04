<template>
  <section class="dashboard-hero" :aria-label="APP_NAME">
    <canvas
      ref="canvasRef"
      class="dashboard-particles"
      :class="{ 'is-hidden': particlesHidden }"
      aria-hidden="true"
    />
    <div v-show="showWordmark" class="dashboard-wordmark">{{ APP_NAME }}</div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

import { APP_NAME } from "../config/app";

interface Particle {
  x: number;
  y: number;
  sx: number;
  sy: number;
  ox: number;
  oy: number;
  tx: number;
  ty: number;
  vx: number;
  vy: number;
  size: number;
  hue: number;
}

const canvasRef = ref<HTMLCanvasElement | null>(null);
const showWordmark = ref(false);
const particlesHidden = ref(false);
let particles: Particle[] = [];
let frameId = 0;
let startTime = 0;

const spreadDuration = 760;
const assembleDuration = 2300;
const holdDuration = 650;
const shrinkDuration = 850;
const fontFamily = "Segoe UI, Microsoft YaHei, Arial, sans-serif";

onMounted(() => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  restartParticles(canvas);
});

onBeforeUnmount(() => {
  cancelAnimationFrame(frameId);
  frameId = 0;
});

function restartParticles(canvas: HTMLCanvasElement) {
  cancelAnimationFrame(frameId);
  setupParticles(canvas);
  frameId = requestAnimationFrame(draw);
}

function setupParticles(canvas: HTMLCanvasElement) {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  showWordmark.value = false;
  particlesHidden.value = false;
  const targets = textTargets(canvas.width, canvas.height, rect.width, rect.height, dpr);
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const centerJitter = Math.min(canvas.width, canvas.height) * 0.035;
  particles = targets.map((target, index) => ({
    x: centerX + randomOffset(centerJitter),
    y: centerY + randomOffset(centerJitter),
    sx: centerX + randomOffset(centerJitter),
    sy: centerY + randomOffset(centerJitter),
    ...spreadPoint(canvas.width, canvas.height, dpr),
    tx: target.x,
    ty: target.y,
    vx: 0,
    vy: 0,
    size: (1.3 + Math.random() * 2.1) * dpr,
    hue: 205 + (index % 90)
  }));
  startTime = performance.now();
}

function textTargets(width: number, height: number, cssWidth: number, cssHeight: number, dpr: number) {
  const buffer = document.createElement("canvas");
  const context = buffer.getContext("2d", { willReadFrequently: true });
  if (!context) return [];
  buffer.width = width;
  buffer.height = height;
  const fontSize = targetFontSize(context, cssWidth, cssHeight, dpr);
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#fff";
  context.font = `700 ${fontSize}px ${fontFamily}`;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(APP_NAME, width / 2, height / 2);
  const image = context.getImageData(0, 0, width, height).data;
  const step = Math.max(4, Math.round((cssWidth < 700 ? 4 : 5) * dpr));
  const points: Array<{ x: number; y: number }> = [];
  for (let y = 0; y < height; y += step) {
    for (let x = 0; x < width; x += step) {
      if (image[(y * width + x) * 4 + 3] > 80) {
        points.push({ x, y });
      }
    }
  }
  return points;
}

function targetFontSize(
  context: CanvasRenderingContext2D,
  cssWidth: number,
  cssHeight: number,
  dpr: number
) {
  const minSize = cssWidth < 560 ? 72 : 96;
  let cssSize = Math.min(196, Math.max(minSize, cssWidth * 0.14, cssHeight * 0.32));
  const maxWidth = cssWidth * dpr * 0.86;
  const maxHeight = cssHeight * dpr * 0.46;

  while (cssSize > 56) {
    const physicalSize = cssSize * dpr;
    context.font = `700 ${physicalSize}px ${fontFamily}`;
    const metrics = context.measureText(APP_NAME);
    const textHeight =
      (metrics.actualBoundingBoxAscent || physicalSize * 0.72) +
      (metrics.actualBoundingBoxDescent || physicalSize * 0.18);

    if (metrics.width <= maxWidth && textHeight <= maxHeight) {
      return physicalSize;
    }
    cssSize -= 4;
  }

  return Math.max(56, cssSize) * dpr;
}

function spreadPoint(width: number, height: number, dpr: number) {
  const padding = 18 * dpr;
  if (Math.random() < 0.58) {
    return {
      ox: padding + Math.random() * Math.max(1, width - padding * 2),
      oy: padding + Math.random() * Math.max(1, height - padding * 2)
    };
  }

  const centerX = width / 2;
  const centerY = height / 2;
  const angle = Math.random() * Math.PI * 2;
  const radius = 0.32 + Math.sqrt(Math.random()) * 0.68;
  return {
    ox: clamp(centerX + Math.cos(angle) * width * 0.54 * radius, padding, width - padding),
    oy: clamp(centerY + Math.sin(angle) * height * 0.54 * radius, padding, height - padding)
  };
}

function draw(now: number) {
  const canvas = canvasRef.value;
  const context = canvas?.getContext("2d");
  if (!canvas || !context) return;
  const elapsed = now - startTime;
  const spreadProgress = Math.min(1, elapsed / spreadDuration);
  const assembleElapsed = Math.max(0, elapsed - spreadDuration);
  const assembleProgress = Math.min(1, assembleElapsed / assembleDuration);
  const shrinkProgress = Math.max(
    0,
    Math.min(1, (assembleElapsed - assembleDuration - holdDuration) / shrinkDuration)
  );
  context.clearRect(0, 0, canvas.width, canvas.height);
  for (const particle of particles) {
    if (shrinkProgress <= 0) {
      if (assembleElapsed <= 0) {
        const spreadEase = easeOutCubic(spreadProgress);
        particle.x = mix(particle.sx, particle.ox, spreadEase);
        particle.y = mix(particle.sy, particle.oy, spreadEase);
      } else {
        const drift = Math.sin(now / 700 + particle.hue) * (1 - assembleProgress) * 20;
        const ax = (particle.tx + drift - particle.x) * (0.012 + assembleProgress * 0.047);
        const ay = (particle.ty - particle.y) * (0.012 + assembleProgress * 0.047);
        particle.vx = (particle.vx + ax) * 0.82;
        particle.vy = (particle.vy + ay) * 0.82;
        particle.x += particle.vx;
        particle.y += particle.vy;
      }
    }
    const shrinkEase = easeInOutCubic(shrinkProgress);
    const x = mix(particle.x, canvas.width / 2, shrinkEase);
    const y = mix(particle.y, canvas.height / 2, shrinkEase);
    const phaseProgress = Math.max(spreadProgress * 0.7, assembleProgress);
    const alpha = (0.24 + phaseProgress * 0.6) * (1 - shrinkEase);
    const size = particle.size * (1 - shrinkEase * 0.72);
    context.fillStyle = `hsla(${particle.hue}, 88%, ${58 + assembleProgress * 10}%, ${alpha})`;
    context.beginPath();
    context.arc(x, y, size, 0, Math.PI * 2);
    context.fill();
  }
  if (shrinkProgress >= 1) {
    context.clearRect(0, 0, canvas.width, canvas.height);
    particlesHidden.value = true;
    showWordmark.value = true;
    frameId = 0;
    return;
  }
  frameId = requestAnimationFrame(draw);
}

function easeOutCubic(value: number) {
  return 1 - Math.pow(1 - value, 3);
}

function easeInOutCubic(value: number) {
  return value < 0.5 ? 4 * value * value * value : 1 - Math.pow(-2 * value + 2, 3) / 2;
}

function mix(from: number, to: number, progress: number) {
  return from + (to - from) * progress;
}

function randomOffset(size: number) {
  return (Math.random() - 0.5) * size;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
</script>
