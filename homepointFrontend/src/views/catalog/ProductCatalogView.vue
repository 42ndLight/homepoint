<template>
  <div class="p-4">
    <!-- Top toolbar -->
    <div class="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-3 mb-4">
      <h1 class="text-2xl font-bold whitespace-nowrap">Product Catalog</h1>

      <div class="flex flex-col sm:flex-row gap-2 sm:items-center w-full xl:w-auto">
        <CategoryFilter
          v-model="selectedCategory"
          class="w-full sm:w-auto"
        />
        <Button
          icon="pi pi-refresh"
          label="Sync"
          @click="handleSync"
          :loading="syncing"
        />
      </div>
    </div>

    <DataView
      v-if="!loading"
      :value="filteredProducts"
      layout="grid"
      :paginator="true"
      :rows="12"
      sortField="name"
      :sortOrder="1"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      :rowsPerPageOptions="[12, 24, 48]"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords}"
    >
      <template #grid="slotProps">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
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
import { ref, computed, onMounted } from 'vue'
import DataView       from 'primevue/dataview'
import Button         from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import { useToast }   from 'primevue/usetoast'
import ProductCard    from '@/components/product/ProductCard.vue'
import CategoryFilter from '@/components/product/CategoryFilter.vue'
import { getProducts, syncProducts } from '@/services/dbService'
import { useCartStore } from '@/stores/cart'

const toast     = useToast()
const cartStore = useCartStore()

const products         = ref([])
const loading          = ref(true)
const syncing          = ref(false)
const selectedCategory = ref(null)

// category_id is stored flat on each product in Dexie (from syncProducts)
const filteredProducts = computed(() =>
  selectedCategory.value
    ? products.value.filter(p => p.category_id === selectedCategory.value)
    : products.value
)

const loadProducts = async () => {
  loading.value = true
  try {
    products.value = await getProducts()
  } catch (err) {
    console.error('Failed to load products:', err)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load products', life: 3000 })
  } finally {
    loading.value = false
  }
}

const handleSync = async () => {
  syncing.value = true
  try {
    await syncProducts()
    await loadProducts()
    toast.add({ severity: 'success', summary: 'Sync Complete', detail: 'Products synchronized successfully', life: 3000 })
  } catch (err) {
    console.error('Sync error:', err)
    toast.add({ severity: 'error', summary: 'Sync Failed', detail: 'Failed to synchronize products', life: 3000 })
  } finally {
    syncing.value = false
  }
}

const handleAddToCart = ({ product, variant }) => {
  if (!variant) {
    toast.add({ severity: 'info', summary: 'No Variants', detail: 'This product has no sellable variants', life: 2000 })
    return
  }
  if (variant.stock_status === 'out_of_stock') {
    toast.add({ severity: 'warn', summary: 'Out of Stock', detail: `${variant.sku} is out of stock`, life: 2000 })
    return
  }

  cartStore.addItem({
    ...variant,
    name: product.name,
    image: variant.image || product.image,
  }, 1)

  toast.add({ severity: 'success', summary: 'Added to Cart', detail: `${product.name} — ${variant.sku}`, life: 2000 })
}

onMounted(async () => {
  // Load from Dexie immediately; sync only if DB is empty
  await loadProducts()
  if (!products.value.length) await handleSync()
})
</script>