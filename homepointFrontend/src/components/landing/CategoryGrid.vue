<template>
  <div class="category-grid">
    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div v-for="i in 6" :key="`skeleton-${i}`" class="animate-pulse">
        <div class="bg-gray-200 h-40 rounded-lg mb-3"></div>
        <div class="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
    </div>

    <div v-else-if="categories.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <CategoryCard
        v-for="category in categories"
        :key="category.id"
        :category="category"
        @click="$emit('selectCategory', category)"
      />
    </div>

    <div v-else class="text-center py-12">
      <p class="text-gray-500 text-lg">No categories available</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import CategoryCard from './CategoryCard.vue'
import { useCategories } from '@/composables/useLanding'

const categories = ref([])
const loading = ref(true)

const { fetchCategories } = useCategories()

onMounted(async () => {
  try {
    categories.value = await fetchCategories()
  } catch (error) {
    console.error('Failed to fetch categories:', error)
    // Fallback to empty array, error already handled in composable
  } finally {
    loading.value = false
  }
})

defineEmits(['selectCategory'])
</script>

<style scoped>
.category-grid {
  width: 100%;
}
</style>
