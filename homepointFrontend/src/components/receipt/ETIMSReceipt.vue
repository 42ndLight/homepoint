<template>
  <div id="receipt-content" class="receipt-page max-w-sm mx-auto bg-white p-6 font-mono text-sm">
    <!-- Store Header -->
    <div class="text-center border-b border-gray-400 pb-4 mb-4">
      <h1 class="font-bold text-lg tracking-wide">{{ storeInfo.name }}</h1>
      <p class="text-xs text-gray-700">{{ storeInfo.address }}</p>
      <p class="text-xs text-gray-700">TIN: {{ storeInfo.tin }}</p>
      <p class="text-xs text-gray-700">{{ storeInfo.phone }}</p>
    </div>

    <!-- Receipt Metadata -->
    <div class="text-center border-b border-gray-400 pb-4 mb-4">
      <p class="font-semibold">INVOICE #{{ receiptData.invoiceNumber }}</p>
      <p class="text-xs text-gray-700">{{ receiptData.date }} {{ receiptData.time }}</p>
      <p class="text-xs text-gray-700">Order #{{ receiptData.orderId }}</p>
    </div>

    <!-- Items Table -->
    <div class="border-b border-gray-400 pb-4 mb-4">
      <!-- Header -->
      <div class="grid grid-cols-4 gap-2 font-bold text-xs mb-2 pb-2 border-b border-gray-300">
        <div>Item</div>
        <div class="text-right">Qty</div>
        <div class="text-right">Price</div>
        <div class="text-right">Total</div>
      </div>

      <!-- Items -->
      <div v-for="item in receiptData.items" :key="item.id" class="text-xs mb-3">
        <!-- Product name and SKU -->
        <div class="font-semibold truncate">
          {{ item.variant?.product?.name || 'Product' }}
        </div>
        <div class="text-gray-600 text-xs">
          SKU: {{ item.variant?.sku }}
        </div>

        <!-- Qty, Price, Total -->
        <div class="grid grid-cols-4 gap-2 mt-1">
          <div />
          <div class="text-right">
            {{ formatQuantity(item.quantity, item.variant?.unit_type) }}
          </div>
          <div class="text-right">{{ formatCurrency(item.price_at_purchase) }}</div>
          <div class="text-right font-semibold">
            {{ formatCurrency(item.quantity * item.price_at_purchase) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Totals Section -->
    <div class="border-b border-gray-400 pb-4 mb-4">
      <div class="flex justify-between text-xs mb-2">
        <span>Subtotal:</span>
        <span>{{ formatCurrency(receiptData.subtotal) }}</span>
      </div>
      <div class="flex justify-between text-xs mb-2 font-semibold">
        <span>VAT (16%):</span>
        <span>{{ formatCurrency(receiptData.vat) }}</span>
      </div>
      <div class="flex justify-between font-bold text-sm border-t border-gray-300 pt-2">
        <span>TOTAL:</span>
        <span>{{ formatCurrency(receiptData.total) }}</span>
      </div>
    </div>

    <!-- QR Code -->
    <div class="text-center mb-4">
      <p class="text-xs text-gray-600 mb-2">eTIMS QR Code</p>
      <img
        v-if="qrCodeData"
        :src="qrCodeData"
        alt="eTIMS QR Code"
        class="w-32 h-32 mx-auto border border-gray-300"
      />
    </div>

    <!-- Footer -->
    <div class="text-center border-t border-gray-400 pt-4">
      <p class="text-xs text-gray-600 mb-2">Thank you for your purchase!</p>
      <p class="text-xs text-gray-600">Payment: {{ paymentMethod }}</p>
      <p class="text-xs text-gray-600">{{ receiptData.date }} {{ receiptData.time }}</p>
      <p class="text-xs text-gray-600 mt-2">Powered by HOMEPOINT POS</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  formatReceiptData,
  generateQRCode,
  formatCurrency,
  formatQuantity,
  getStoreInfo,
} from '@/utils/receiptFormatter'

const props = defineProps({
  order: {
    type: Object,
    required: true,
  },
  paymentMethod: {
    type: String,
    default: 'M-Pesa',
  },
})

const storeInfo = computed(() => getStoreInfo())
const receiptData = computed(() => formatReceiptData(props.order))
const qrCodeData = ref(null)

onMounted(async () => {
  qrCodeData.value = await generateQRCode(receiptData.value)
})

// Expose functions for template
const exposedFormatCurrency = formatCurrency
const exposedFormatQuantity = formatQuantity
</script>

<style scoped>
.receipt-page {
  width: 80mm;
  min-height: 100%;
  margin-left: auto;
  margin-right: auto;
}

@media (max-width: 640px) {
  .receipt-page {
    width: 100%;
    padding: 1rem;
  }
}

/* Ensure proper printing */
@media print {
  @page {
    size: 80mm auto;
    margin: 0;
  }

  body {
    margin: 0;
    padding: 0;
  }

  .receipt-page {
    box-shadow: none;
    page-break-after: always;
  }
}
</style>
