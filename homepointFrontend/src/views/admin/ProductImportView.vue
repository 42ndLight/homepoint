<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-800">Product Import</h1>
      <p class="text-gray-600 mt-1">Import products, variants, and inventory data from Excel files</p>
    </div>

    <!-- File Uploader Component -->
    <FileUploader />
  </div>
</template>

<script setup>
import FileUploader from '@/components/admin/FileUploader.vue'
</script>
