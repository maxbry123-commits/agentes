<template>
  <canvas ref="canvasRef" class="particle-canvas"></canvas>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animationId: number | null = null

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  color: string
  alpha: number
  alphaChange: number
}

onMounted(() => {
  if (!canvasRef.value) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const resizeCanvas = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  
  // 粒子配置
  const particleCount = 50
  const particles: Particle[] = []
  const colors = [
    'rgba(0, 212, 255, ',   // 青色
    'rgba(139, 92, 246, ',  // 紫色
    'rgba(59, 130, 246, ', // 蓝色
    'rgba(16, 185, 129, ', // 绿色
  ]
  
  // 初始化粒子
  const initParticles = () => {
    particles.length = 0
    for (let i = 0; i < particleCount; i++) {
      particles.push(createParticle())
    }
  }
  
  const createParticle = (): Particle => {
    const color = colors[Math.floor(Math.random() * colors.length)]
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: Math.random() * 2 + 0.5,
      color,
      alpha: Math.random() * 0.5 + 0.1,
      alphaChange: (Math.random() - 0.5) * 0.01
    }
  }
  
  // 绘制粒子
  const drawParticles = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // 绘制连接线
    ctx.lineWidth = 0.5
    for (let i = 0; i < particles.length; i++) {
      const p1 = particles[i]
      
      // 绘制粒子
      ctx.beginPath()
      ctx.arc(p1.x, p1.y, p1.size, 0, Math.PI * 2)
      ctx.fillStyle = p1.color + p1.alpha + ')'
      ctx.fill()
      
      // 绘制连线
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j]
        const dx = p1.x - p2.x
        const dy = p1.y - p2.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        
        if (dist < 150) {
          ctx.beginPath()
          ctx.moveTo(p1.x, p1.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.strokeStyle = p1.color + (0.15 * (1 - dist / 150)) + ')'
          ctx.stroke()
        }
      }
    }
  }
  
  // 更新粒子
  const updateParticles = () => {
    particles.forEach(p => {
      p.x += p.vx
      p.y += p.vy
      
      // 边界检测
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1
      
      // 透明度变化
      p.alpha += p.alphaChange
      if (p.alpha > 0.6 || p.alpha < 0.1) {
        p.alphaChange *= -1
      }
    })
  }
  
  // 动画循环
  const animate = () => {
    updateParticles()
    drawParticles()
    animationId = requestAnimationFrame(animate)
  }
  
  initParticles()
  animate()
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})
</script>

<style scoped>
.particle-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
</style>
