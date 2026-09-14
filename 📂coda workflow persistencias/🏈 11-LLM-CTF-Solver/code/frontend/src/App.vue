<script setup lang="ts">
import AppSidebar from '@/components/AppSidebar.vue'
</script>

<template>
  <div class="flex h-screen">
    <AppSidebar />
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>
