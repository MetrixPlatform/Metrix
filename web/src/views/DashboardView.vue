<template>
  <section class="dashboard-hero" aria-label="Metrix">
    <canvas
      ref="canvasRef"
      class="dashboard-particles"
      :class="{ 'is-hidden': particlesHidden }"
      aria-hidden="true"
    />
    <div v-show="showWordmark" class="dashboard-wordmark">Metrix</div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

interface Particle {
  x: number;
  y: number;
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
let resizeObserver: ResizeObserver | null = null;
let startTime = 0;

const assembleDuration = 2400;
const holdDuration = 650;
const shrinkDuration = 850;

onMounted(() => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  resizeObserver = new ResizeObserver(() => restartParticles(canvas));
  resizeObserver.observe(canvas);
  restartParticles(canvas);
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
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
  const targets = textTargets(canvas.width, canvas.height);
  particles = targets.map((target, index) => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    tx: target.x,
    ty: target.y,
    vx: 0,
    vy: 0,
    size: 1.2 + Math.random() * 1.9,
    hue: 205 + (index % 90)
  }));
  startTime = performance.now();
}

function textTargets(width: number, height: number) {
  const buffer = document.createElement("canvas");
  const context = buffer.getContext("2d", { willReadFrequently: true });
  if (!context) return [];
  buffer.width = width;
  buffer.height = height;
  const fontSize = width < 700 ? 76 : 118;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#fff";
  context.font = `700 ${fontSize}px Segoe UI, Microsoft YaHei, Arial, sans-serif`;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText("Metrix", width / 2, height / 2);
  const image = context.getImageData(0, 0, width, height).data;
  const step = width < 700 ? 5 : 6;
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

function draw(now: number) {
  const canvas = canvasRef.value;
  const context = canvas?.getContext("2d");
  if (!canvas || !context) return;
  const elapsed = now - startTime;
  const assembleProgress = Math.min(1, elapsed / assembleDuration);
  const shrinkProgress = Math.max(
    0,
    Math.min(1, (elapsed - assembleDuration - holdDuration) / shrinkDuration)
  );
  context.clearRect(0, 0, canvas.width, canvas.height);
  for (const particle of particles) {
    if (shrinkProgress <= 0) {
      const drift = Math.sin(now / 700 + particle.hue) * (1 - assembleProgress) * 18;
      const ax = (particle.tx + drift - particle.x) * (0.012 + assembleProgress * 0.045);
      const ay = (particle.ty - particle.y) * (0.012 + assembleProgress * 0.045);
      particle.vx = (particle.vx + ax) * 0.82;
      particle.vy = (particle.vy + ay) * 0.82;
      particle.x += particle.vx;
      particle.y += particle.vy;
    }
    const shrinkEase = easeInOutCubic(shrinkProgress);
    const x = mix(particle.x, canvas.width / 2, shrinkEase);
    const y = mix(particle.y, canvas.height / 2, shrinkEase);
    const alpha = (0.34 + assembleProgress * 0.5) * (1 - shrinkEase);
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

function easeInOutCubic(value: number) {
  return value < 0.5 ? 4 * value * value * value : 1 - Math.pow(-2 * value + 2, 3) / 2;
}

function mix(from: number, to: number, progress: number) {
  return from + (to - from) * progress;
}
</script>
