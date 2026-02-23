<!-- PosItemCard.vue -->
<template>
  <div 
    class="group relative border rounded-xl overflow-hidden bg-white shadow-sm hover:shadow-md transition-all duration-150 cursor-pointer select-none"
    :class="{
      'opacity-60 pointer-events-none': isOutOfStock,
      'border-red-300 bg-red-50/30': isLowStock && !isOutOfStock,
      'hover:border-primary-400': !isOutOfStock
    }"
    @click="handleAdd"
  >
    <!-- Image -->
    <div class="relative h-32 sm:h-36 md:h-40 bg-gray-100 flex items-center justify-center overflow-hidden">
      <img 
        v-if="item.image"
        :src="item.image" 
        :alt="item.display_name"
        class="w-full h-full object-cover"
        loading="lazy"
      />
      <div v-else class="text-gray-300">
        <i class="pi pi-image text-5xl" />
      </div>

      <!-- Stock badge overlay -->
      <div class="absolute top-2 right-2">
        <Tag 
          :value="stockLabel" 
          :severity="stockSeverity"
          class="text-xs font-medium px-2 py-1 shadow-sm"
        />
      </div>
    </div>

    <!-- Content -->
    <div class="p-3 space-y-1.5">
      <!-- Name -->
      <div class="font-medium text-gray-900 line-clamp-2 min-h-[2.8rem] text-sm sm:text-base">
        {{ item.display_name || item.name }}
      </div>

      <!-- Price + Stock row -->
      <div class="flex items-baseline justify-between gap-2">
        <div class="text-xl sm:text-2xl font-bold text-primary-600">
          KES {{ formatPrice(item.price) }}
        </div>

        <div class="text-right">
          <div class="text-xs text-gray-500">Stock</div>
          <div 
            class="font-semibold text-sm sm:text-base"
            :class="stockTextClass"
          >
            {{ item.stock_quantity.toLocaleString() }}
          </div>
        </div>
      </div>

      <!-- Unit / SKU (optional but helpful in hardware stores) -->
      <div v-if="item.unit || item.sku" class="text-xs text-gray-500 truncate">
        {{ item.unit ? `${item.unit}` : '' }} 
        <span v-if="item.unit && item.sku"> • </span>
        {{ item.sku || '' }}
      </div>
    </div>

    <!-- Quick add hint (only shown on hover/touch) -->
    <div class="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-3 pointer-events-none">
      <div class="bg-primary-600 text-white text-sm font-medium px-4 py-1.5 rounded-full shadow-md">
        Tap to add →
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Tag from 'primevue/tag'

const props = defineProps({
  item: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['add-to-cart'])

const formatPrice = (price) => {
  if (typeof price !== 'number' || isNaN(price)) return '0.00'
  return price.toLocaleString('en-KE', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })
}

const isOutOfStock = computed(() => (props.item.stock_quantity ?? 0) <= 0)
const isLowStock = computed(() => {
  const qty = props.item.stock_quantity ?? 0
  const threshold = props.item.low_stock_threshold ?? 10
  return qty > 0 && qty <= threshold
})

const stockLabel = computed(() => {
  if (isOutOfStock.value) return 'Out of Stock'
  if (isLowStock.value) return 'Low Stock'
  return 'In Stock'
})

const stockSeverity = computed(() => {
  if (isOutOfStock.value) return 'danger'
  if (isLowStock.value) return 'warn'
  return 'success'
})

const stockTextClass = computed(() => {
  if (isOutOfStock.value) return 'text-red-600'
  if (isLowStock.value) return 'text-orange-600 font-bold'
  return 'text-green-700'
})

const handleAdd = () => {
  if (!isOutOfStock.value) {
    emit('add-to-cart', props.item)
  }
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