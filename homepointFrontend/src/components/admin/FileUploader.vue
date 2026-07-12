<template>
  <div class="p-6 bg-white rounded-lg shadow-md">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <i class="pi pi-upload"></i>
        Import Products
      </h2>
      <p class="text-gray-600 text-sm mt-2">Upload an Excel file (.xlsx) to import products, variants, and inventory</p>
    </div>

    <!-- Upload Area or Status -->
    <div v-if="!isProcessing && !taskCompleted" class="mb-6">
      <!-- File Input -->
      <div
        @drop="onDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        :class="[
          'border-2 border-dashed rounded-lg p-8 text-center transition cursor-pointer',
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-blue-400'
        ]"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx"
          @change="onFileSelected"
          class="hidden"
        />

        <div @click="$refs.fileInput.click()" class="cursor-pointer">
          <i class="pi pi-cloud-upload text-4xl text-blue-500 mb-3 block"></i>
          <p class="text-lg font-semibold text-gray-800 mb-2">
            Click to upload or drag and drop
          </p>
          <p class="text-sm text-gray-600">
            Excel files (.xlsx) up to 10 MB
          </p>
        </div>

        <!-- Selected File Info -->
        <div v-if="selectedFile" class="mt-4 pt-4 border-t border-gray-300">
          <div class="flex items-center justify-center gap-2 text-green-600">
            <i class="pi pi-check-circle"></i>
            <span class="font-medium">{{ selectedFile.name }}</span>
            <span class="text-gray-600">({{ formatFileSize(selectedFile.size) }})</span>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
        <div class="flex gap-3">
          <i class="pi pi-exclamation-circle text-red-500 flex-shrink-0 mt-0.5"></i>
          <div>
            <p class="font-semibold text-red-800">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Upload Button -->
      <div class="mt-6 flex gap-3">
        <button
          v-if="selectedFile"
          @click="uploadFile"
          :disabled="isUploading"
          class="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 transition flex items-center justify-center gap-2"
        >
          <i v-if="!isUploading" class="pi pi-upload"></i>
          <i v-else class="pi pi-spin pi-spinner"></i>
          {{ isUploading ? 'Uploading...' : 'Upload File' }}
        </button>
        <button
          v-if="selectedFile"
          @click="clearSelection"
          class="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Processing State -->
    <div v-else-if="isProcessing" class="mb-6">
      <div class="p-8 bg-blue-50 border border-blue-200 rounded-lg text-center">
        <i class="pi pi-spin pi-spinner text-4xl text-blue-500 mb-4 block"></i>
        <p class="text-lg font-semibold text-gray-800 mb-2">Processing your file...</p>
        <p class="text-sm text-gray-600">
          Please wait while we import your data. Do not close this window.
        </p>
        
        <!-- Progress Info -->
        <div v-if="taskStatus" class="mt-4 text-sm text-gray-700">
          <p>Status: <span class="font-semibold">{{ taskStatus.status }}</span></p>
          <p class="text-xs text-gray-500 mt-2">Task ID: {{ taskStatus.task_id }}</p>
        </div>
      </div>
    </div>

    <!-- Completion State - Success -->
    <div v-else-if="taskCompleted && !taskError" class="mb-6">
      <div class="p-8 bg-green-50 border border-green-200 rounded-lg">
        <div class="flex items-start gap-4">
          <i class="pi pi-check-circle text-4xl text-green-500 flex-shrink-0"></i>
          <div class="flex-1">
            <p class="text-lg font-semibold text-green-800 mb-2">Import Completed Successfully!</p>
            <p class="text-sm text-green-700 mb-4">
              Your products, variants, and inventory have been imported into the system.
            </p>
            <button
              @click="reset"
              class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
            >
              Import Another File
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Completion State - Error -->
    <div v-else-if="taskCompleted && taskError" class="mb-6">
      <div class="p-8 bg-red-50 border border-red-200 rounded-lg">
        <div class="flex items-start gap-4">
          <i class="pi pi-times-circle text-4xl text-red-500 flex-shrink-0"></i>
          <div class="flex-1">
            <p class="text-lg font-semibold text-red-800 mb-2">Import Failed</p>
            <p class="text-sm text-red-700 mb-2 font-mono bg-red-100 p-3 rounded break-words">
              {{ taskError }}
            </p>
            <button
              @click="reset"
              class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Info Box -->
    <div class="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <p class="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
        <i class="pi pi-info-circle"></i>
        File Format Requirements
      </p>
      <ul class="text-sm text-gray-700 space-y-1 ml-6">
        <li>• Must be in Excel (.xlsx) format</li>
        <li>• Maximum file size: 10 MB</li>
        <li>• Must contain sheets: Categories, Products, Variants, Inventory</li>
        <li>• First row should be headers, second row can be notes</li>
        <li>• Data starts from row 3</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import fileImportService from '@/services/fileImportService'

// State
const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const isProcessing = ref(false)
const taskCompleted = ref(false)
const error = ref(null)
const taskStatus = ref(null)
const taskError = ref(null)

// Computed
const taskId = computed(() => taskStatus.value?.task_id)

// Methods
const onFileSelected = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    selectFile(file)
  }
}

const onDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files?.[0]
  if (file) {
    selectFile(file)
  }
}

const selectFile = (file) => {
  error.value = null
  
  // Validate file
  const validation = fileImportService.validateFile(file)
  if (!validation.valid) {
    error.value = validation.error
    selectedFile.value = null
    return
  }

  selectedFile.value = file
}

const clearSelection = () => {
  selectedFile.value = null
  error.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  error.value = null

  try {
    const response = await fileImportService.uploadFile(selectedFile.value)
    taskStatus.value = response
    isUploading.value = false
    isProcessing.value = true
    selectedFile.value = null

    // Start polling
    pollTaskStatus()
  } catch (err) {
    isUploading.value = false
    error.value = err.data?.error || err.message || 'Failed to upload file'
  }
}

const pollTaskStatus = async () => {
  if (!taskId.value) return

  try {
    const status = await fileImportService.getTaskStatus(taskId.value)
    taskStatus.value = status

    if (status.status === 'COMPLETED') {
      isProcessing.value = false
      taskCompleted.value = true
      taskError.value = null
    } else if (status.status === 'FAILED') {
      isProcessing.value = false
      taskCompleted.value = true
      taskError.value = status.error_msg || 'Import failed for unknown reason'
    } else {
      // Still processing, poll again in 3 seconds
      setTimeout(pollTaskStatus, 3000)
    }
  } catch {
    // Network error during polling, retry
    setTimeout(pollTaskStatus, 3000)
  }
}

const reset = () => {
  selectedFile.value = null
  isUploading.value = false
  isProcessing.value = false
  taskCompleted.value = false
  error.value = null
  taskStatus.value = null
  taskError.value = null
  isDragging.value = false
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>
