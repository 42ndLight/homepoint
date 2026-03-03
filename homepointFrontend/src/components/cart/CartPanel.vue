<template>
  <Panel header="Cart" class="h-full flex flex-col">
    <template #header>
      <div class="flex items-center justify-between w-full">
        <span class="font-semibold">Cart</span>
        <span v-if="cartStore.items.length" class="text-sm text-gray-500">
          {{ cartStore.itemCount }} item(s)
        </span>
      </div>
    </template>

    <div v-if="cartStore.items.length === 0" class="flex flex-col items-center justify-center py-12 text-gray-500">
      <i class="pi pi-shopping-cart text-4xl mb-3 opacity-50"></i>
      <p>Cart is empty</p>
      <p class="text-sm mt-1">Search or scan to add items</p>
    </div>

    <div v-else class="flex flex-col flex-1 min-h-0">
      <div class="overflow-y-auto flex-1 -mx-4 px-4">
        <CartItem
          v-for="item in cartStore.items"
          :key="item.variant_id"
          :item="item"
          @remove="cartStore.removeItem(item.variant_id)"
          @update-quantity="(qty) => cartStore.updateQuantity(item.variant_id, qty)"
        />
      </div>

      <div class="border-t border-gray-200 pt-4 mt-4 space-y-2">
        <div class="flex justify-between text-sm text-gray-600">
          <span>Subtotal</span>
          <span>KES {{ formatPrice(cartStore.subtotal) }}</span>
        </div>
        <div class="flex justify-between text-sm text-gray-600">
          <span>VAT (16%)</span>
          <span>KES {{ formatPrice(cartStore.vat) }}</span>
        </div>
        <div class="flex justify-between font-semibold text-lg pt-2">
          <span>Total</span>
          <span>KES {{ formatPrice(cartStore.total) }}</span>
        </div>
        <Button
          label="Checkout"
          icon="pi pi-credit-card"
          class="w-full mt-4"
          size="large"
          :disabled="cartStore.items.length === 0"
          @click="$emit('checkout')"
        />
      </div>
    </div>
  </Panel>
</template>

<script setup>
import Panel from 'primevue/panel'
import Button from 'primevue/button'
import CartItem from './CartItem.vue'
import Checkout from '../checkout/CheckoutForm.vue'
import { useCartStore } from '@/stores/cart'
import { useOrderStore } from '@/stores/order'

defineEmits(['checkout'])

const cartStore = useCartStore()
const order = useOrderStore()

const formatPrice = (price) => {
  if (!price && price !== 0) return '0.00'
  return Number.parseFloat(price).toFixed(2)
}
</script>
