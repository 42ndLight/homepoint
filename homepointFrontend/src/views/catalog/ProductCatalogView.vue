<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">Product Catalog</h1>
      <Button 
        icon="pi pi-refresh" 
        label="Sync" 
        @click="handleSync"
        :loading="syncing"
      />
    </div>

    <CategoryFilter v-model="selectedCategory" @change="handleCategoryChange" />

    <DataView
      v-if="!loading"
      :value="filteredProducts"
      :layout="layout"
      :paginator="true"
      :rows="12"
      :sortOrder="1"
      sortField="name"
    >
      <template #grid="slotProps">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <ProductCard
            v-for="product in slotProps.items"
            :key="product.id"
            :product="product"
            @add-to-cart="handleAddToCart"
          />
        </div>
      </template>

      <template #empty>
        <div class="text-center py-8">
          <i class="pi pi-inbox text-4xl text-gray-400 mb-2"></i>
          <p class="text-gray-500">No products found</p>
        </div>
      </template>
    </DataView>

    <div v-else class="flex justify-center items-center py-8">
      <ProgressSpinner />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import DataView from 'primevue/dataview'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import { useToast } from 'primevue/usetoast'
import ProductCard from '@/components/product/ProductCard.vue'
import CategoryFilter from '@/components/product/CategoryFilter.vue'
import { getProducts, syncProducts } from '@/services/dbService'
import { useCartStore } from '@/stores/cart'

const toast = useToast()
const cartStore = useCartStore()

const products = ref([])
const loading = ref(true)
const syncing = ref(false)
const layout = ref('grid')
const selectedCategory = ref(null)

const filteredProducts = computed(() => {
  if (!selectedCategory.value) {
    return products.value
  }
  return products.value.filter(p => p.category_id === selectedCategory.value)
})

const handleSync = async () => {
  syncing.value = true
  try {
    await syncProducts()
    await loadProducts()
    toast.add({
      severity: 'success',
      summary: 'Sync Complete',
      detail: 'Products synchronized successfully',
      life: 3000,
    })
  } catch (error) {
    console.error('Sync error:', error)
    toast.add({
      severity: 'error',
      summary: 'Sync Failed',
      detail: 'Failed to synchronize products',
      life: 3000,
    })
  } finally {
    syncing.value = false
  }
}

const loadProducts = async () => {
  loading.value = true
  try {
    products.value = await getProducts()
  } catch (error) {
    console.error('Failed to load products:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load products',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

const handleCategoryChange = (categoryId) => {
  selectedCategory.value = categoryId
}

const handleAddToCart = (product) => {
  // If product has variants, we'll need to show a variant selector
  // For now, add the first variant or base product
  if (product.variants && product.variants.length > 0) {
    const variant = product.variants[0]
    cartStore.addItem(variant, 1)
    toast.add({
      severity: 'success',
      summary: 'Added to Cart',
      detail: `${product.name} added to cart`,
      life: 2000,
    })
  } else {
    toast.add({
      severity: 'info',
      summary: 'Select Variant',
      detail: 'Please select a variant to add to cart',
      life: 2000,
    })
  }
}

onMounted(async () => {
  // Try to sync on mount if no products in DB
  try {
    const existingProducts = await getProducts()
    if (existingProducts.length === 0) {
      await handleSync()
    } else {
      await loadProducts()
    }
  } catch (error) {
    console.error('Initial load error:', error)
    await loadProducts()
  }
})
</script>

