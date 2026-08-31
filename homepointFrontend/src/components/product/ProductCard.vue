<template>
  <Card class="h-full flex flex-col">
    <template #header>
      <div class="h-40 bg-gray-100 flex items-center justify-center overflow-hidden">
        <i class="pi pi-image text-4xl text-gray-400" v-if="!activeImage"></i>
        <img v-else :src="activeImage" :alt="product.name" class="w-full h-full object-cover" />
      </div>
    </template>

    <template #title>
      <!-- Variant name first, product name secondary -->
      <div class="leading-tight">
        <div class="text-base font-bold text-gray-900 truncate">{{ activeVariantLabel }}</div>
        <div class="text-xs text-gray-500 truncate mt-0.5">{{ product.name }}</div>
      </div>
    </template>

    <template #subtitle>
      <div class="flex items-center gap-2 flex-wrap mt-1">
        <Tag :value="categoryName" severity="info" />
        <Tag :value="stockTag.label" :severity="stockTag.severity" />
      </div>
    </template>

    <template #content>
      <div class="space-y-3">
        <!-- Active variant price -->
        <div class="text-xl font-bold text-primary">
          KES {{ formatPrice(activeVariant?.price ?? product.base_price) }}
          <span class="text-xs font-normal text-gray-500 ml-1">/ {{ activeVariant?.unit_type_display ?? 'unit' }}</span>
        </div>

        <!-- Variant selector — show all variants as chips -->
        <div v-if="product.variants?.length > 1">
          <div class="text-xs text-gray-500 mb-1">Variants ({{ product.variants.length }})</div>
          <div class="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
            <button
              v-for="v in product.variants"
              :key="v.id"
              @click.stop="selectedVariantId = v.id"
              :class="[
                'px-2 py-0.5 rounded text-xs border transition-colors',
                v.id === selectedVariantId
                  ? 'bg-primary text-white border-primary'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-primary',
                v.stock_status === 'out_of_stock' ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'
              ]"
              :disabled="v.stock_status === 'out_of_stock'"
              :title="variantLabel(v)"
            >
              {{ variantChipLabel(v) }}
            </button>
          </div>
        </div>

        <p class="text-xs text-gray-500 line-clamp-2">{{ product.description }}</p>
      </div>
    </template>

    <template #footer>
      <Button
        label="Add to Cart"
        icon="pi pi-shopping-cart"
        class="w-full"
        :disabled="activeVariant?.stock_status === 'out_of_stock'"
        @click="$emit('add-to-cart', { product, variant: activeVariant })"
      />
    </template>
  </Card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Card   from 'primevue/card'
import Tag    from 'primevue/tag'
import Button from 'primevue/button'

const props = defineProps({
  product: { type: Object, required: true },
})

defineEmits(['add-to-cart'])

// ── Variant selection ────────────────────────────────────────────────────────
// Default to first in-stock variant, fall back to first overall
const defaultVariant = computed(() => {
  const variants = props.product.variants ?? []
  return (
    variants.find(v => v.stock_status === 'in_stock') ??
    variants.find(v => v.stock_status === 'low_stock') ??
    variants[0] ??
    null
  )
})

const selectedVariantId = ref(defaultVariant.value?.id ?? null)

// Reset selection when product changes (e.g. list re-renders)
watch(() => props.product.id, () => {
  selectedVariantId.value = defaultVariant.value?.id ?? null
})

const activeVariant = computed(() =>
  props.product.variants?.find(v => v.id === selectedVariantId.value) ?? defaultVariant.value
)

// ── Labels ───────────────────────────────────────────────────────────────────
const variantLabel = (v) => {
  const attrs = Object.values(v.attributes ?? {}).join(' • ')
  return attrs || v.sku
}

const variantChipLabel = (v) => {
  // Keep chips short: prefer attribute values, else last part of SKU
  const attrs = Object.values(v.attributes ?? {})
  if (attrs.length) return attrs.join(' ')
  const skuParts = v.sku.split(/[-_\s]/)
  return skuParts[skuParts.length - 1] || v.sku
}

const activeVariantLabel = computed(() => {
  if (!activeVariant.value) return props.product.name
  return variantLabel(activeVariant.value) || activeVariant.value.sku
})

const categoryName = computed(() =>
  props.product.category_detail?.name ?? 'Uncategorized'
)

const activeImage = computed(() =>
  activeVariant.value?.image || props.product.image || null
)

// ── Price ────────────────────────────────────────────────────────────────────
const formatPrice = (price) => {
  if (price == null || Number.isNaN(price)) return '0.00'
  return Number.parseFloat(price).toLocaleString('en-KE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

// ── Stock ────────────────────────────────────────────────────────────────────
const stockStatus = computed(() => activeVariant.value?.stock_status ?? 'in_stock')

const stockTag = computed(() => {
  switch (stockStatus.value) {
    case 'in_stock':  return { label: 'In Stock',     severity: 'success' }
    case 'low_stock': return { label: 'Low Stock',    severity: 'warn'    }
    default:          return { label: 'Out of Stock', severity: 'danger'  }
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
