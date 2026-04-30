<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <div class="p-6 border-b border-gray-100">
      <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
        <i class="pi pi-book text-blue-600"></i>
        Operational Procedures
      </h2>
    </div>
    <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="guide in guides" :key="guide.title" class="space-y-3">
        <h3 class="font-bold text-gray-900 flex items-center gap-2">
          <i :class="guide.icon" class="text-blue-500"></i>
          {{ guide.title }}
        </h3>
        <ul class="space-y-2">
          <li v-for="step in guide.steps" :key="step" class="text-sm text-gray-600 flex gap-2">
            <span class="text-blue-500">•</span>
            {{ step }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  guides: Array
})
</script>
