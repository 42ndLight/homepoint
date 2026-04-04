<template>
  <div class="p-4">
    <!-- Header with Search -->
    <div class="mb-6">
      <div class="flex flex-col md:flex-row gap-4 mb-4">
        <div class="flex-1">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by SKU or product name..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            @input="debounceSearch"
          />
        </div>
        <button
          @click="loadInventory"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 whitespace-nowrap"
        >
          <i class="pi pi-refresh" :class="{ 'animate-spin': isLoading }"></i>
          Refresh
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800 font-semibold">Error Loading Inventory</p>
      <p class="text-red-700 text-sm mt-1">{{ error }}</p>
      <button
        @click="clearError"
        class="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
      >
        Dismiss
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && inventory.length === 0" class="space-y-4">
      <div v-for="i in 5" :key="i" class="bg-gray-200 h-12 rounded animate-pulse"></div>
    </div>

    <!-- DataTable -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <DataTable
        :value="inventory"
        :loading="isLoading"
        :paginator="true"
        :rows="10"
        :total-records="totalRecords"
        responsive-layout="scroll"
        class="p-datatable-striped"
        @page="onPageChange"
      >
        <template #empty>
          <div class="py-8 text-center text-gray-500">
            <i class="pi pi-inbox text-4xl mb-2"></i>
            <p>No inventory items found</p>
          </div>
        </template>

        <Column field="id" header="ID" :style="{ width: '60px' }" sortable>
          <template #body="{ data }">
            <span class="text-sm font-medium">{{ data.id }}</span>
          </template>
        </Column>

        <Column field="product_name" header="Product Name" sortable>
          <template #body="{ data }">
            <div>
              <p class="font-medium text-gray-900">{{ data.product_name }}</p>
              <p class="text-xs text-gray-600">SKU: {{ data.sku }}</p>
            </div>
          </template>
        </Column>

        <Column field="quantity" header="Current Stock" :style="{ width: '120px' }">
          <template #body="{ data }">
            <div class="flex items-center gap-2">
              <span class="font-semibold text-lg">{{ data.quantity }}</span>
              <span
                class="px-2 py-1 rounded text-xs font-semibold"
                :class="getStatusClass(data.quantity)"
              >
                {{ getStatusLabel(data.quantity) }}
              </span>
            </div>
          </template>
        </Column>

        <Column field="reorder_point" header="Reorder Point" :style="{ width: '120px' }">
          <template #body="{ data }">
            <span class="text-sm">{{ data.reorder_point || 'N/A' }}</span>
          </template>
        </Column>

        <Column header="Actions" :style="{ width: '200px' }">
          <template #body="{ data }">
            <div class="flex gap-2">
              <button
                @click="openEditDialog(data)"
                class="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition text-xs font-semibold flex items-center gap-1"
              >
                <i class="pi pi-pencil"></i>
                Edit
              </button>
              <button
                @click="confirmDelete(data)"
                class="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition text-xs font-semibold flex items-center gap-1"
                v-if="canDelete"
              >
                <i class="pi pi-trash"></i>
                Delete
              </button>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Edit Dialog -->
    <Dialog v-model:visible="editDialogVisible" header="Edit Stock" :modal="true" :style="{ width: '400px' }">
      <template v-if="editingItem">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">Product</label>
            <p class="text-gray-900 font-medium">{{ editingItem.product_name }}</p>
            <p class="text-xs text-gray-600">SKU: {{ editingItem.sku }}</p>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">Current Quantity</label>
            <p class="text-lg font-bold text-gray-900">{{ editingItem.quantity }}</p>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">New Quantity</label>
            <input
              v-model.number="newQuantity"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter new quantity"
            />
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">Notes (Optional)</label>
            <textarea
              v-model="updateNotes"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Stock received, physical count, etc."
              rows="3"
            ></textarea>
          </div>

          <div class="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
            <p class="font-semibold mb-1">Quantity Change</p>
            <p>
              {{ editingItem.quantity }} → <span class="font-bold">{{ newQuantity !== null ? newQuantity : 'N/A' }}</span>
            </p>
          </div>
        </div>
      </template>

      <template #footer>
        <button
          @click="editDialogVisible = false"
          class="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition"
        >
          Cancel
        </button>
        <button
          @click="saveStock"
          :disabled="isUpdating || newQuantity === null"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:opacity-50"
        >
          <i class="pi pi-check mr-2" :class="{ 'animate-spin': isUpdating }"></i>
          {{ isUpdating ? 'Saving...' : 'Save' }}
        </button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InventoryService from '@/services/inventoryService'

const toast = useToast()

const inventory = ref([])
const isLoading = ref(false)
const isUpdating = ref(false)
const error = ref(null)
const searchQuery = ref('')
const totalRecords = ref(0)
const currentPage = ref(0)
const pageSize = ref(10)

const editDialogVisible = ref(false)
const editingItem = ref(null)
const newQuantity = ref(null)
const updateNotes = ref('')

const canDelete = ref(false) // Set based on user permissions

let searchTimeout = null

const debounceSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 0
    loadInventory()
  }, 300)
}

const loadInventory = async () => {
  isLoading.value = true
  error.value = null

  try {
    const response = await InventoryService.getInventory({
      search: searchQuery.value,
      limit: pageSize.value,
      offset: currentPage.value * pageSize.value,
    })

    if (Array.isArray(response)) {
      inventory.value = response
      totalRecords.value = response.length
    } else if (response.results) {
      inventory.value = response.results
      totalRecords.value = response.count || response.results.length
    } else {
      inventory.value = []
      totalRecords.value = 0
    }
  } catch (err) {
    error.value = err.message || 'Failed to load inventory'
    console.error('Inventory load error:', err)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.value,
      life: 3000,
    })
  } finally {
    isLoading.value = false
  }
}

const openEditDialog = (item) => {
  editingItem.value = { ...item }
  newQuantity.value = item.quantity
  updateNotes.value = ''
  editDialogVisible.value = true
}

const saveStock = async () => {
  if (newQuantity.value === null || !editingItem.value) return

  isUpdating.value = true

  try {
    await InventoryService.updateStock(
      editingItem.value.id,
      newQuantity.value,
      updateNotes.value
    )

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `Stock updated from ${editingItem.value.quantity} to ${newQuantity.value}`,
      life: 3000,
    })

    editDialogVisible.value = false
    await loadInventory()
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.message || 'Failed to update stock',
      life: 3000,
    })
    console.error('Stock update error:', err)
  } finally {
    isUpdating.value = false
  }
}

const confirmDelete = (item) => {
  if (confirm(`Delete inventory item "${item.product_name}"? This action cannot be undone.`)) {
    deleteInventory(item)
  }
}

const deleteInventory = async (item) => {
  // Implementation depends on backend support
  // For now, just show a message
  toast.add({
    severity: 'info',
    summary: 'Info',
    detail: 'Delete functionality coming soon',
    life: 3000,
  })
}

const getStatusLabel = (quantity) => {
  return InventoryService.getStockStatus(quantity)
}

const getStatusClass = (quantity) => {
  const status = InventoryService.getStockStatus(quantity)
  return InventoryService.getStatusColor(status)
}

const onPageChange = (event) => {
  currentPage.value = event.page
  pageSize.value = event.rows
  loadInventory()
}

const clearError = () => {
  error.value = null
}

onMounted(() => {
  loadInventory()
})
</script>
