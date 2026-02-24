<template>
  <div class="cart-item flex gap-3 py-3 border-b border-gray-200 last:border-b-0">
    <div class="flex-1 min-w-0">
      <div class="font-medium text-gray-900 truncate">{{ item.name }}</div>
      <div class="text-xs text-gray-500">{{ item.sku }}</div>
    </div>
    <div class="flex items-center gap-2 flex-shrink-0">
      <InputNumber
        v-model="quantity"
        :min="0.01"
        :minFractionDigits="0"
        :maxFractionDigits="4"
        mode="decimal"
        :useGrouping="false"
        inputClass="w-16 text-center text-sm"
        @update:modelValue="handleQuantityChange"
      />
    </div>
    <div class="flex flex-col items-end flex-shrink-0 w-24">
      <span class="text-sm text-gray-600">KES {{ formatPrice(item.price) }}</span>
      <span class="font-semibold text-gray-900">KES {{ formatPrice(lineTotal) }}</span>
    </div>
    <Button
      icon="pi pi-trash"
      severity="secondary"
      text
      rounded
      size="small"
      :aria-label="'Remove ' + item.name"
      @click="$emit('remove')"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['remove', 'update-quantity'])

const quantity = ref(Number.parseFloat(props.item.quantity) || 1)

watch(() => props.item.quantity, (val) => {
  const q = Number.parseFloat(val)
  if (!Number.isNaN(q) && q !== quantity.value) {
    quantity.value = q
  }
})

const lineTotal = computed(() => {
  const price = Number.parseFloat(props.item.price || 0)
  const qty = Number.parseFloat(quantity.value || 0)
  return Math.round(price * qty * 100) / 100
})

const formatPrice = (price) => {
  if (!price && price !== 0) return '0.00'
  return Number.parseFloat(price).toFixed(2)
}

const handleQuantityChange = (value) => {
  if (value != null && value > 0) {
    const qty = typeof value === 'number' ? value : Number.parseFloat(value)
    if (!Number.isNaN(qty)) {
      quantity.value = qty
      emit('update-quantity', qty)
    }
  }
}
</script>
