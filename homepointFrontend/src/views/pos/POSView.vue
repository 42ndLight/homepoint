<template>
  <div class="pos-layout flex h-[calc(100vh-8rem)] gap-4 p-4">
    <!-- Left: Product search & grid -->
    <div class="flex-1 flex flex-col min-w-0">
      <div class="flex justify-between items-center mb-4 gap-4">
        <h1 class="text-2xl font-bold">Point of Sale</h1>
        <div class="flex gap-2">
          <ProductSearch
            class="flex-1 min-w-[280px]"
            @select="handleProductSelected"
          />
          <Button
            icon="pi pi-barcode"
            label="Scan Barcode"
            @click="showScanner = true"
            outlined
          />
        </div>
      </div>

      <div class="flex-1 overflow-auto">
        <DataView
          v-if="!loading"
          :value="sellableItems"
          :layout="'grid'"
        >
          <template #grid="slotProps">
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              <PosItemCard
                v-for="item in slotProps.items"
                :key="item.id"
                :item="item"
                @add-to-cart="handleAddToCart"
              />
            </div>
          </template>
          <template #empty>
            <div class="text-center py-12">
              <i class="pi pi-inbox text-4xl text-gray-400 mb-2"></i>
              <p class="text-gray-500">No products found</p>
              <p class="text-sm text-gray-400 mt-1">Sync products or check your connection</p>
            </div>
          </template>
        </DataView>
        <div v-else class="flex justify-center items-center py-12">
          <ProgressSpinner />
        </div>
      </div>
    </div>

    <!-- Right: Cart panel -->
    <div class="w-96 flex-shrink-0">
      <CartPanel @checkout="handleCheckout" />
    </div>

    <Dialog
      v-model:visible="showScanner"
      modal
      :header="null"
      :contentStyle="{ padding: 0 }"
      :style="{ width: 'min(90vw, 400px)' }"
      :dismissableMask="true"
      :closable="false"
      @hide="showScanner = false"
    >
      <BarcodeScanner
        :visible="showScanner"
        @close="showScanner = false"
      />
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import DataView from 'primevue/dataview'
import ProgressSpinner from 'primevue/progressspinner'
import ProductSearch from '@/components/search/ProductSearch.vue'
import PosItemCard from '@/components/product/PosItemCard.vue'
import CartPanel from '@/components/cart/CartPanel.vue'
import BarcodeScanner from '@/components/barcode/BarcodeScanner.vue'
import { getSellableItems, syncProducts } from '@/services/dbService'
import { useCartStore } from '@/stores/cart'
import { useToast } from 'primevue/usetoast'

const showScanner = ref(false)
const sellableItems = ref([])
const loading = ref(true)

const cartStore = useCartStore()
const toast = useToast()


const handleSync = async () => {
  syncing.value = true
  try {
    await syncProducts()
    await loadSellableItems()
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


const loadSellableItems = async () => {
  loading.value = true
  try {
    sellableItems.value = await getSellableItems()
  } catch (error) {
    console.error('Failed to load product variants:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load product variants',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

const handleAddToCart = (item) => {          // item = variant-like object from getSellableItems
  cartStore.addItem(item, 1)

  toast.add({
    severity: 'success',
    summary: 'Added',
    detail: `${item.display_name || item.name} × 1 added`,
    life: 1800,
  })
}

const handleProductSelected = () => {
  // ProductSearch already adds to cart on select; toast is shown there
}

const handleCheckout = () => {
  if (cartStore.items.length === 0) return
  toast.add({
    severity: 'info',
    summary: 'Checkout',
    detail: 'Checkout flow coming soon',
    life: 3000,
  })
}

onMounted(loadSellableItems)
</script>
