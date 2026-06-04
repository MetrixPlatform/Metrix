<template>
  <section class="dashboard-hero" aria-label="Metrix">
    <canvas ref="canvasRef" class="dashboard-particles" aria-hidden="true" />
    <div class="dashboard-wordmark">Metrix</div>
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
let particles: Particle[] = [];
let frameId = 0;
let resizeObserver: ResizeObserver | null = null;
let startTime = 0;

onMounted(() => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  resizeObserver = new ResizeObserver(() => setupParticles(canvas));
  resizeObserver.observe(canvas);
  setupParticles(canvas);
  startTime = performance.now();
  frameId = requestAnimationFrame(draw);
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  cancelAnimationFrame(frameId);
});

function setupParticles(canvas: HTMLCanvasElement) {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
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
  const progress = Math.min(1, (now - startTime) / 2400);
  context.clearRect(0, 0, canvas.width, canvas.height);
  for (const particle of particles) {
    const drift = Math.sin(now / 700 + particle.hue) * (1 - progress) * 18;
    const ax = (particle.tx + drift - particle.x) * (0.012 + progress * 0.045);
    const ay = (particle.ty - particle.y) * (0.012 + progress * 0.045);
    particle.vx = (particle.vx + ax) * 0.82;
    particle.vy = (particle.vy + ay) * 0.82;
    particle.x += particle.vx;
    particle.y += particle.vy;
    const alpha = 0.34 + progress * 0.5;
    context.fillStyle = `hsla(${particle.hue}, 88%, ${58 + progress * 10}%, ${alpha})`;
    context.beginPath();
    context.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
    context.fill();
  }
  frameId = requestAnimationFrame(draw);
}
</script>
