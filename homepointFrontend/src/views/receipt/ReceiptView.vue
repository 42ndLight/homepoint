<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Receipt</h1>
          <p class="text-gray-600 mt-1" v-if="orderId">Order #{{ orderId }}</p>
        </div>
        <div class="flex gap-3">
          <PButton
            icon="pi pi-arrow-left"
            label="Back"
            class="p-button-secondary"
            @click="$router.back()"
          />
          <PButton
            icon="pi pi-print"
            label="Print"
            class="p-button-primary"
            @click="printReceipt"
          />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center py-12">
        <ProgressSpinner />
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
        <p class="text-red-700">{{ error }}</p>
        <PButton
          label="Try Again"
          class="p-button-primary mt-4"
          @click="fetchOrder"
        />
      </div>

      <!-- Receipt Display -->
      <div v-else-if="order" class="bg-white rounded-lg shadow">
        <div class="p-8">
          <ETIMSReceipt :order="order" :paymentMethod="paymentMethod" />
        </div>

        <!-- Actions -->
        <div class="border-t border-gray-200 p-6 flex gap-3 justify-center">
          <PButton
            icon="pi pi-download"
            label="Download PDF"
            class="p-button-secondary"
            @click="downloadPDF"
            :loading="downloading"
          />
          <PButton
            icon="pi pi-copy"
            label="Copy Receipt"
            class="p-button-secondary"
            @click="copyReceipt"
          />
          <PButton
            icon="pi pi-home"
            label="New Order"
            class="p-button-primary"
            @click="newOrder"
          />
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <i class="pi pi-inbox text-4xl text-gray-400 mb-3"></i>
        <p class="text-gray-600">No order found</p>
      </div>
    </div>

    <!-- Toast for notifications -->
    <Toast />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import PButton from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import Toast from 'primevue/toast'
import ETIMSReceipt from '@/components/receipt/ETIMSReceipt.vue'
import { formatReceiptData } from '@/utils/receiptFormatter'
import { useOrderStore } from '@/stores/order'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const orderStore = useOrderStore()

const downloading = ref(false)

const orderId = computed(() => route.params.orderId || route.query.orderId)
const order = computed(() => orderStore.currentOrder)
const loading = computed(() => orderStore.loading)
const error = computed(() => orderStore.error)
const paymentMethod = computed(() => 
  order.value?.payment_method === 'cash' ? 'Cash' : 'M-Pesa'
)

onMounted(async () => {
  if (orderId.value) {
    const result = await orderStore.fetchOrder(orderId.value)
    if (!result.success) {
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: result.error || 'Failed to load receipt',
        life: 5000,
      })
    }
  }
})

const fetchOrder = async () => {
  if (orderId.value) {
    const result = await orderStore.fetchOrder(orderId.value)
    if (!result.success) {
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: result.error || 'Failed to load receipt',
        life: 5000,
      })
    }
  }
}

const printReceipt = () => {
  window.print()
}

const downloadPDF = async () => {
  if (!order.value) return

  downloading.value = true

  try {
    // Dynamic import of html2pdf to reduce bundle size
    const html2pdf = (await import('html2pdf.js')).default

    const receiptData = formatReceiptData(order.value)
    const element = document.getElementById('receipt-content')

    if (!element) {
      throw new Error('Receipt element not found')
    }

    const options = {
      margin: 5,
      filename: `Receipt-${receiptData.invoiceNumber}.pdf`,
      image: { type: 'image/png', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { orientation: 'portrait', unit: 'mm', format: [80, 297] },
    }

    html2pdf().set(options).from(element).save()

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Receipt downloaded successfully',
      life: 3000,
    })
  } catch (err) {
    console.error('Error downloading PDF:', err)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to download receipt. Try printing instead.',
      life: 5000,
    })
  } finally {
    downloading.value = false
  }
}

const copyReceipt = async () => {
  try {
    const receiptText = document.getElementById('receipt-content')?.innerText

    if (!receiptText) {
      throw new Error('Receipt not found')
    }

    await navigator.clipboard.writeText(receiptText)

    toast.add({
      severity: 'success',
      summary: 'Copied',
      detail: 'Receipt copied to clipboard',
      life: 3000,
    })
  } catch (err) {
    console.error('Error copying receipt:', err)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to copy receipt',
      life: 3000,
    })
  }
}

const newOrder = () => {
  router.push('/pos')
}
</script>

<style scoped>
@media print {
  :deep(.p-button),
  .border-t {
    display: none !important;
  }

  .max-w-4xl {
    max-width: 100%;
  }

  :deep(.receipt-page) {
    box-shadow: none;
  }
}
</style>
