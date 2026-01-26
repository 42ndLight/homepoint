<template>
  <div class="relative">
    <span class="p-input-icon-left w-full">
      <i class="pi pi-search" />
      <InputText
        v-model="searchQuery"
        placeholder="Search products (e.g., 'cemnt' for Cement)..."
        class="w-full"
        @input="handleSearch"
        @focus="showResults = true"
        @blur="handleBlur"
      />
    </span>

    <!-- Search Results Dropdown -->
    <Panel
      v-if="showResults && searchResults.length > 0"
      class="absolute z-50 w-full mt-1 max-h-96 overflow-y-auto"
      :style="{ top: '100%' }"
    >
      <div class="space-y-2">
        <div
          v-for="product in searchResults"
          :key="product.id"
          class="p-2 hover:bg-gray-100 cursor-pointer rounded"
          @click="handleSelectProduct(product)"
        >
          <div class="font-semibold" v-html="highlightMatch(product.name, searchQuery)"></div>
          <div class="text-sm text-gray-600">
            <span v-if="product.category">{{ product.category.name }}</span>
            <span v-if="product.variants && product.variants.length > 0" class="ml-2">
              - KES {{ formatPrice(getMinPrice(product)) }}
            </span>
          </div>
          <div v-if="product.variants && product.variants.length > 0" class="text-xs text-gray-500 mt-1">
            SKU: {{ product.variants.map(v => v.sku).join(', ') }}
          </div>
        </div>
      </div>
    </Panel>

    <!-- No Results -->
    <Panel
      v-if="showResults && searchQuery && searchResults.length === 0 && !loading"
      class="absolute z-50 w-full mt-1"
      :style="{ top: '100%' }"
    >
      <div class="text-center py-4 text-gray-500">
        No products found for "{{ searchQuery }}"
      </div>
    </Panel>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import Panel from 'primevue/panel'
import { useProductSearch } from '@/composables/useProductSearch'
import { useCartStore } from '@/stores/cart'
import { useToast } from 'primevue/usetoast'
import { debounce } from '@/utils/debounce'

const props = defineProps({
  modelValue: String,
})

const emit = defineEmits(['update:modelValue', 'select'])

const cartStore = useCartStore()
const toast = useToast()
const { searchQuery, searchResults, loading, initializeSearch, highlightMatch } = useProductSearch()

const showResults = ref(false)

// Debounce search input
const handleSearch = debounce(() => {
  emit('update:modelValue', searchQuery.value)
}, 300)

const handleBlur = () => {
  // Delay hiding to allow click events
  setTimeout(() => {
    showResults.value = false
  }, 200)
}

const handleSelectProduct = (product) => {
  // If product has variants, add first variant
  if (product.variants && product.variants.length > 0) {
    const variant = product.variants[0]
    cartStore.addItem(variant, 1)
    toast.add({
      severity: 'success',
      summary: 'Added to Cart',
      detail: `${product.name} added to cart`,
      life: 2000,
    })
  }
  
  emit('select', product)
  searchQuery.value = ''
  showResults.value = false
}

const formatPrice = (price) => {
  if (!price) return '0.00'
  return parseFloat(price).toFixed(2)
}

const getMinPrice = (product) => {
  if (!product.variants || product.variants.length === 0) {
    return product.base_price
  }
  return Math.min(...product.variants.map(v => parseFloat(v.price)))
}

onMounted(() => {
  initializeSearch()
})
</script>

<style scoped>
:deep(mark) {
  background-color: yellow;
  padding: 0;
}
</style>

