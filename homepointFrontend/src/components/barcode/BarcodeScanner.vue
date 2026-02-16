<template>
  <div class="barcode-scanner">
    <div class="scanner-header flex justify-between items-center mb-3">
      <h3 class="text-lg font-semibold">Scan Barcode</h3>
      <Button
        icon="pi pi-times"
        severity="secondary"
        text
        rounded
        aria-label="Close"
        @click="handleClose"
      />
    </div>

    <Message v-if="errorMessage" severity="error" :closable="false" class="mb-3">
      {{ errorMessage }}
    </Message>

    <div
      ref="scannerContainer"
      id="barcode-scanner-viewport"
      class="scanner-viewport"
      :class="{ 'opacity-0': !isScanning && !errorMessage }"
    >
      <!-- Quagga injects video/canvas here -->
    </div>

    <p v-if="isScanning" class="text-sm text-gray-600 mt-2 text-center">
      Point your camera at a barcode (EAN, UPC, or Code 128)
    </p>

    <div class="flex gap-2 mt-4 justify-end">
      <Button label="Cancel" severity="secondary" @click="handleClose" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useBarcodeScanner } from '@/composables/useBarcodeScanner'
import { getProductBySKU } from '@/services/dbService'
import { useCartStore } from '@/stores/cart'
import { useToast } from 'primevue/usetoast'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['scan', 'close'])

const toast = useToast()
const cartStore = useCartStore()
const scannerContainer = ref(null)
const errorMessage = ref(null)

const lastScannedCode = ref(null)
const SCAN_COOLDOWN_MS = 1500

const handleBarcodeDetected = async (code) => {
  if (!code) return

  const now = Date.now()
  if (lastScannedCode.value?.code === code && now - lastScannedCode.value.time < SCAN_COOLDOWN_MS) {
    return // Ignore duplicate scans within cooldown
  }
  lastScannedCode.value = { code, time: now }

  try {
    const product = await getProductBySKU(String(code).trim())

    if (!product) {
      toast.add({
        severity: 'warn',
        summary: 'Product not found',
        detail: `No product found for barcode: ${code}`,
        life: 4000,
      })
      return
    }

    const variant = product.variant
    if (!variant) {
      toast.add({
        severity: 'warn',
        summary: 'No variant',
        detail: 'Product has no variant to add',
        life: 3000,
      })
      return
    }

    // Merge product name into variant for cart display
    const variantWithName = { ...variant, name: product.name }

    cartStore.addItem(variantWithName, 1)

    toast.add({
      severity: 'success',
      summary: 'Added to cart',
      detail: `${product.name} (${variant.sku})`,
      life: 3000,
    })

    emit('scan', { code, product })
    handleClose()
  } catch (err) {
    console.error('Barcode lookup failed:', err)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to add product to cart',
      life: 4000,
    })
  }
}

const { isScanning, error, start, stop } = useBarcodeScanner({
  onDetected: handleBarcodeDetected,
})

const startScanner = async () => {
  errorMessage.value = null

  if (!scannerContainer.value) {
    errorMessage.value = 'Scanner container not ready.'
    return
  }

  try {
    await start({
      inputStream: {
        target: scannerContainer.value,
      },
    })
  } catch (err) {
    console.error('Scanner init error:', err)
    if (err?.name === 'NotAllowedError' || err?.message?.toLowerCase().includes('permission')) {
      errorMessage.value = 'Camera permission denied. Please allow camera access to scan barcodes.'
    } else if (err?.name === 'NotFoundError') {
      errorMessage.value = 'No camera found on this device.'
    } else {
      errorMessage.value = err?.message || 'Failed to start camera. Please try again.'
    }
  }
}

const handleClose = () => {
  stop()
  errorMessage.value = null
  emit('close')
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      startScanner()
    } else {
      stop()
    }
  }
)

onMounted(() => {
  if (props.visible) {
    startScanner()
  }
})
</script>

<style scoped>
.barcode-scanner {
  padding: 0.5rem;
}

.scanner-viewport {
  position: relative;
  width: 100%;
  min-height: 240px;
  background: #000;
  border-radius: 0.5rem;
  overflow: hidden;
}

.scanner-viewport :deep(video) {
  width: 100%;
  height: auto;
  display: block;
}

.scanner-viewport :deep(canvas) {
  display: none;
}
</style>
