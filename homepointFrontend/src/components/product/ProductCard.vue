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
      <Tag :value="product.category?.name || 'Uncategorized'" severity="info" />
    </template>
    <template #content>
      <div class="space-y-2">
        <p class="text-sm text-gray-600 line-clamp-2">{{ product.description }}</p>
        
        <!-- Price Range -->
        <div v-if="product.variants && product.variants.length > 0">
          <div class="text-sm text-gray-500">Price Range:</div>
          <div class="text-lg font-bold text-primary">
            KES {{ formatPrice(getMinPrice()) }} - KES {{ formatPrice(getMaxPrice()) }}
          </div>
        </div>
        <div v-else class="text-lg font-bold text-primary">
          KES {{ formatPrice(product.base_price) }}
        </div>

        <!-- Stock Status -->
        <div v-if="hasLowStock()" class="mt-2">
          <Tag value="Low Stock" severity="warn" />
        </div>
        <div v-else-if="hasInStock()" class="mt-2">
          <Tag value="In Stock" severity="success" />
        </div>
        <div v-else class="mt-2">
          <Tag value="Out of Stock" severity="danger" />
        </div>
      </div>
    </template>
    <template #footer>
      <Button 
        label="Add to Cart" 
        icon="pi pi-shopping-cart" 
        class="w-full"
        :disabled="!hasInStock()"
        @click="$emit('add-to-cart', product)"
      />
    </template>
  </Card>
</template>

<script setup>
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import { computed } from 'vue'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
})

defineEmits(['add-to-cart'])

const formatPrice = (price) => {
  if (!price) return '0.00'
  return parseFloat(price).toFixed(2)
}

const getMinPrice = () => {
  if (!props.product.variants || props.product.variants.length === 0) {
    return props.product.base_price
  }
  return Math.min(...props.product.variants.map(v => parseFloat(v.price)))
}

const getMaxPrice = () => {
  if (!props.product.variants || props.product.variants.length === 0) {
    return props.product.base_price
  }
  return Math.max(...props.product.variants.map(v => parseFloat(v.price)))
}

const hasInStock = () => {
  if (!props.product.variants || props.product.variants.length === 0) {
    return true // Assume in stock if no variants
  }
  return props.product.variants.some(v => {
    const inv = v.inventory || {}
    return inv.quantity > 0
  })
}

const hasLowStock = () => {
  if (!props.product.variants || props.product.variants.length === 0) {
    return false
  }
  return props.product.variants.some(v => {
    const inv = v.inventory || {}
    const threshold = v.stock_threshold || 10
    return inv.quantity > 0 && inv.quantity <= threshold
  })
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

