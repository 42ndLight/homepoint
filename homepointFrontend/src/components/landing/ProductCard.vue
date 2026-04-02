<template>
  <div class="product-card rounded-lg shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden bg-white">
    <div class="relative h-48 bg-gray-100 overflow-hidden group">
      <img
        :src="product.image || `https://via.placeholder.com/200/E5E7EB/666666?text=${product.name}`"
        :alt="product.name"
        class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
      />
      <div v-if="product.category" class="absolute top-2 right-2 bg-blue-600 text-white text-xs px-2 py-1 rounded">
        {{ product.category }}
      </div>
    </div>
    <div class="p-4">
      <h3 class="font-bold text-gray-900 text-sm line-clamp-2">{{ product.name }}</h3>
      <p v-if="product.sku" class="text-xs text-gray-500 mt-1">SKU: {{ product.sku }}</p>

      <!-- Price hidden for quote-based pricing -->
      <div class="mt-3 pt-3 border-t border-gray-100">
        <p class="text-xs text-gray-600 mb-2">Request a quote for bulk pricing</p>
        <button
          @click="$emit('addToQuote')"
          class="w-full px-3 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          Add to Quote
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  product: {
    type: Object,
    required: true,
  },
})

defineEmits(['addToQuote'])
</script>

<style scoped>
.product-card {
  display: flex;
  flex-direction: column;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
