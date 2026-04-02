<template>
  <div class="product-grid">
    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div v-for="i in 8" :key="`skeleton-${i}`" class="animate-pulse">
        <div class="bg-gray-200 h-48 rounded-lg mb-3"></div>
        <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div class="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div class="h-10 bg-gray-200 rounded"></div>
      </div>
    </div>

    <div v-else-if="products.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <!-- Use existing ProductCard component from catalog -->
      <ProductCard
        v-for="product in products"
        :key="product.id"
        :product="product"
        @add-to-cart="handleAddToQuote"
      />
    </div>

    <div v-else class="text-center py-12">
      <p class="text-gray-500 text-lg">
        {{ error ? 'Unable to load products' : 'No products available' }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import ProductCard from '@/components/product/ProductCard.vue'
import { useProducts } from '@/composables/useLanding'

const props = defineProps({
  categoryId: {
    type: Number,
    default: null,
  },
})

const products = ref([])
const loading = ref(true)
const error = ref(false)

const { fetchProducts } = useProducts()

const loadProducts = async () => {
  loading.value = true
  error.value = false
  try {
    products.value = await fetchProducts(props.categoryId)
  } catch (err) {
    console.error('Failed to fetch products:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

const handleAddToQuote = (product) => {
  // Emit event to parent with product info
  // Parent (LandingPage) will handle adding to quote modal
  emit('addToQuote', product)
}

onMounted(() => {
  loadProducts()
})

watch(() => props.categoryId, () => {
  loadProducts()
})

const emit = defineEmits(['addToQuote'])
</script>

<style scoped>
.product-grid {
  width: 100%;
}
</style>
