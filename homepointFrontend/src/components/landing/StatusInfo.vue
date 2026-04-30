<template>
  <section class="mb-12">
    <!-- Admin View: System Health -->
    <div v-if="isAdmin" class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div v-for="stat in adminStats" :key="stat.label" class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center">
        <i :class="[stat.icon, stat.iconColor]" class="text-3xl mb-2"></i>
        <span class="text-sm text-gray-600">{{ stat.label }}</span>
        <span class="text-xl font-bold text-gray-900">{{ stat.value }}</span>
      </div>
    </div>
    
    <!-- Staff View: Shift Status -->
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div v-for="stat in staffStats" :key="stat.label" class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 class="text-sm font-semibold text-gray-500 uppercase mb-4">{{ stat.title }}</h3>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-2xl font-bold" :class="stat.valueClass || 'text-gray-900'">{{ stat.value }}</p>
            <p class="text-sm text-gray-600">{{ stat.label }}</p>
          </div>
          <i :class="[stat.icon, stat.iconBg]" class="text-3xl p-3 rounded-full"></i>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  isAdmin: Boolean,
  adminStats: Array,
  staffStats: Array
})
</script>
