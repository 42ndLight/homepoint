<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">Point of Sale</h1>
      <Button
        icon="pi pi-barcode"
        label="Scan Barcode"
        @click="showScanner = true"
        outlined
      />
    </div>

    <p class="text-gray-600">POS interface coming soon...</p>

    <Dialog
      v-model:visible="showScanner"
      modal
      :header="null"
      :contentStyle="{ padding: 0 }"
      :style="{ width: 'min(90vw, 400px)' }"
      :dismissableMask="true"
      :closable="false"
      @hide="showScanner = false"
    >
      <BarcodeScanner
        :visible="showScanner"
        @close="showScanner = false"
      />
    </Dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import BarcodeScanner from '@/components/barcode/BarcodeScanner.vue'

const showScanner = ref(false)
</script>

