<template>
  <Card class="h-full">
    <template #header>
      <div class="h-48 bg-gray-200 flex items-center justify-center">
        <i class="pi pi-image text-4xl text-gray-400" v-if="!product.image"></i>
        <img v-else :src="product.image" :alt="product.name" class="w-full h-full object-cover" />
      </div>
    </template>

    <template #title>
      <div class="text-lg font-semibold">{{ product.name }}</div>
    </template>

    <template #subtitle>
      <Tag :value="categoryName" severity="info" />
    </template>

    <template #content>
      <div class="space-y-2">
        <p class="text-sm text-gray-600 line-clamp-2">{{ product.description }}</p>

        <!-- Price range across variants, or base_price fallback -->
        <div v-if="product.variants?.length">
          <div class="text-sm text-gray-500">Price Range:</div>
          <div class="text-lg font-bold text-primary">
            <template v-if="minPrice === maxPrice">
              KES {{ formatPrice(minPrice) }}
            </template>
            <template v-else>
              KES {{ formatPrice(minPrice) }} – KES {{ formatPrice(maxPrice) }}
            </template>
          </div>
        </div>
        <div v-else class="text-lg font-bold text-primary">
          KES {{ formatPrice(product.base_price) }}
        </div>

        <!-- Stock status — reads stock_status label (always present) -->
        <div class="mt-2">
          <Tag :value="stockTag.label" :severity="stockTag.severity" />
        </div>
      </div>
    </template>

    <template #footer>
      <Button
        label="Add to Cart"
        icon="pi pi-shopping-cart"
        class="w-full"
        :disabled="overallStockStatus === 'out_of_stock'"
        @click="$emit('add-to-cart', product)"
      />
    </template>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import Card   from 'primevue/card'
import Tag    from 'primevue/tag'
import Button from 'primevue/button'

const props = defineProps({
  product: { type: Object, required: true },
})
const categoryName = computed(() => {
  return props.product.category_detail?.name ?? 'Uncategorized'         
})

defineEmits(['add-to-cart'])

// ---------------------------------------------------------------------------
// Price
// ---------------------------------------------------------------------------

const formatPrice = (price) => {
  if (price == null || Number.isNaN(price)) return '0.00'
  return Number.parseFloat(price).toLocaleString('en-KE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const minPrice = computed(() => {
  if (!props.product.variants?.length) return props.product.base_price
  return Math.min(...props.product.variants.map(v => Number.parseFloat(v.price ?? 0)))
})

const maxPrice = computed(() => {
  if (!props.product.variants?.length) return props.product.base_price
  return Math.max(...props.product.variants.map(v => Number.parseFloat(v.price ?? 0)))
})

// ---------------------------------------------------------------------------
// Stock — backend sends stock_status on every variant for all roles.
// stock_quantity is only present for staff/admin (null for cashiers).
//
// Priority across all variants:
//   any in_stock  → product is "In Stock"
//   any low_stock → product is "Low Stock"  (only if none are in_stock)
//   all out       → product is "Out of Stock"
// ---------------------------------------------------------------------------

const overallStockStatus = computed(() => {
  const variants = props.product.variants

  // No variants — fall back gracefully
  if (!variants?.length) return 'in_stock'

  // Prefer raw quantity when available (staff view)
  const hasQuantity = variants.some(v => v.stock_quantity != null)

  if (hasQuantity) {
    const anyInStock  = variants.some(v => (v.stock_quantity ?? 0) > (v.stock_threshold ?? 10))
    const anyLowStock = variants.some(v => {
      const qty = v.stock_quantity ?? 0
      return qty > 0 && qty <= (v.stock_threshold ?? 10)
    })
    if (anyInStock)  return 'in_stock'
    if (anyLowStock) return 'low_stock'
    return 'out_of_stock'
  }

  // Cashier path — use server-computed stock_status label
  if (variants.some(v => v.stock_status === 'in_stock'))  return 'in_stock'
  if (variants.some(v => v.stock_status === 'low_stock')) return 'low_stock'
  return 'out_of_stock'
})

const stockTag = computed(() => {
  switch (overallStockStatus.value) {
    case 'in_stock':    return { label: 'In Stock',     severity: 'success' }
    case 'low_stock':   return { label: 'Low Stock',    severity: 'warn'    }
    default:            return { label: 'Out of Stock', severity: 'danger'  }
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>