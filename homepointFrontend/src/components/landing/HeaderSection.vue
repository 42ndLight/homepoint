<template>
  <div class="bg-white border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Welcome, {{ name }}!</h1>
          <p class="text-gray-600 mt-1">
            Internal Resources & Operational Dashboard
          </p>
        </div>
        <div class="flex flex-col text-right">
          <span class="text-sm font-semibold text-blue-600 uppercase tracking-wider">{{ role }}</span>
          <span class="text-xs text-gray-500 mt-1">Last login: {{ lastLogin }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  name: String,
  role: String,
  lastLogin: String
})
</script>
