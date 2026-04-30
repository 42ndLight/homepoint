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
          v-for="item in searchResults"
          :key="item.id"
          class="p-2 hover:bg-gray-100 cursor-pointer rounded border-b border-gray-100 last:border-0"
          @click="handleSelectProduct(item)"
        >
          <div class="font-semibold" v-html="highlightMatch(item.display_name || item.name, searchQuery)"></div>
          <div class="flex justify-between items-center text-sm text-gray-600 mt-1">
            <span class="font-mono text-xs">SKU: {{ item.sku }}</span>
            <span class="font-bold text-primary-600">KES {{ formatPrice(item.price) }}</span>
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

const handleSelectProduct = (item) => {
  // Emit the specific variant/item to the parent (POSView)
  // Parent handles cartStore.addItem(item, 1) and toast notifications
  emit('select', item)
  searchQuery.value = ''
  showResults.value = false
}

const formatPrice = (price) => {
  if (!price) return '0.00'
  return Number.parseFloat(price).toFixed(2)
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

