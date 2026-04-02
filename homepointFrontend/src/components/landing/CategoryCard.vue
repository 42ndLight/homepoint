<template>
  <div
    @click="$emit('click')"
    class="category-card cursor-pointer group overflow-hidden rounded-lg shadow-sm hover:shadow-md transition-all duration-300 hover:scale-105"
  >
    <div class="relative h-40 bg-gray-200 overflow-hidden">
      <img
        :src="category.image || `https://via.placeholder.com/200/2563EB/FFFFFF?text=${category.name}`"
        :alt="category.name"
        class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
      />
      <div class="absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-colors"></div>
    </div>
    <div class="p-4 bg-white">
      <h3 class="font-bold text-gray-900 text-center">{{ category.name }}</h3>
      <p v-if="category.count" class="text-xs text-gray-500 text-center mt-1">
        {{ category.count }} items
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  category: {
    type: Object,
    required: true,
  },
})

defineEmits(['click'])
</script>

<style scoped>
.category-card {
  border-radius: 0.5rem;
  background: white;
}
</style>
