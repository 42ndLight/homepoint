<template>
  <div class="p-4">
    <!-- Header with Product Selection and Search -->
    <div class="mb-6">
      <div class="flex flex-col md:flex-row gap-4 mb-4">
        <div class="flex-1">
          <label class="block text-sm font-semibold text-gray-700 mb-2">Select Product</label>
          <select
            v-model="selectedProductId"
            @change="loadInventory"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">-- Select a product --</option>
            <option v-for="product in products" :key="product.id" :value="product.id">
              {{ product.name }}
            </option>
          </select>
        </div>
        <div class="flex-1">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by SKU or variant..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            @input="debounceSearch"
          />
        </div>
        <button
          @click="loadInventory"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 whitespace-nowrap h-10 mt-6"
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
            <p>{{ selectedProductId ? 'No inventory items found' : 'Select a product to view inventory' }}</p>
          </div>
        </template>

        <Column field="id" header="Variant ID" :style="{ width: '80px' }" sortable>
          <template #body="{ data }">
            <span class="text-sm font-medium">{{ data.id }}</span>
          </template>
        </Column>

        <Column field="sku" header="SKU" sortable>
          <template #body="{ data }">
            <div>
              <p class="font-medium text-gray-900">{{ data.sku }}</p>
              <p class="text-xs text-gray-600" v-if="data.attributes">
                {{ formatAttributes(data.attributes) }}
              </p>
            </div>
          </template>
        </Column>

        <Column field="stock_quantity" header="Current Stock" :style="{ width: '120px' }">
          <template #body="{ data }">
            <div class="flex items-center gap-2">
              <span class="font-semibold text-lg">{{ data.stock_quantity }}</span>
              <span
                class="px-2 py-1 rounded text-xs font-semibold"
                :class="getStatusClass(data.stock_quantity)"
              >
                {{ getStatusLabel(data.stock_quantity) }}
              </span>
            </div>
          </template>
        </Column>

        <Column field="stock_threshold" header="Reorder Point" :style="{ width: '120px' }">
          <template #body="{ data }">
            <span class="text-sm">{{ data.stock_threshold || 'N/A' }}</span>
          </template>
        </Column>

        <Column field="stock_last_updated" header="Last Updated" :style="{ width: '180px' }">
          <template #body="{ data }">
            <span class="text-sm text-gray-700">{{ formatLastUpdated(data.stock_last_updated) }}</span>
          </template>
        </Column>

        <Column field="last_updated" header="Last Updated" :style="{ width: '180px' }">
          <template #body="{ data }">
            <span class="text-sm text-gray-700">{{ formatLastUpdated(data.last_updated) }}</span>
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
            <label class="block text-sm font-semibold text-gray-700 mb-2">Variant</label>
            <p class="text-gray-900 font-medium">{{ editingItem.sku }}</p>
            <p class="text-xs text-gray-600" v-if="editingItem.attributes">
              {{ formatAttributes(editingItem.attributes) }}
            </p>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">Current Quantity</label>
            <p class="text-lg font-bold text-gray-900">{{ editingItem.stock_quantity }}</p>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">Last Updated</label>
            <p class="text-sm text-gray-700">{{ formatLastUpdated(editingItem.stock_last_updated) }}</p>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">Movement Type</label>
            <div class="flex gap-2">
              <button
                @click="movementType = 'IN'"
                :class="[
                  'flex-1 px-4 py-2 rounded font-semibold transition',
                  movementType === 'IN'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                ]"
              >
                <i class="pi pi-plus mr-2"></i>Stock In
              </button>
              <button
                @click="movementType = 'OUT'"
                :class="[
                  'flex-1 px-4 py-2 rounded font-semibold transition',
                  movementType === 'OUT'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                ]"
              >
                <i class="pi pi-minus mr-2"></i>Stock Out
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">Amount to {{ movementType === 'IN' ? 'Add' : 'Remove' }}</label>
            <input
              v-model.number="newQuantity"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="`Enter amount to ${movementType === 'IN' ? 'add' : 'remove'}`"
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
            <p class="font-semibold mb-2">Quantity Change</p>
            <p v-if="movementType === 'IN'" class="mb-1">
              {{ editingItem.stock_quantity }} + {{ newQuantity || 0 }} = <span class="font-bold text-lg text-green-700">{{ (editingItem.stock_quantity || 0) + (newQuantity || 0) }}</span>
            </p>
            <p v-else class="mb-1">
              {{ editingItem.stock_quantity }} - {{ newQuantity || 0 }} = <span class="font-bold text-lg text-blue-700">{{ Math.max(0, (editingItem.stock_quantity || 0) - (newQuantity || 0)) }}</span>
            </p>
            <p class="text-xs text-gray-600 mt-1">{{ movementType === 'IN' ? 'Stock will increase' : 'Stock will decrease' }}</p>
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
import { getProducts } from '@/services/dbService'

const toast = useToast()

const products = ref([])
const inventory = ref([])
const isLoading = ref(false)
const isUpdating = ref(false)
const error = ref(null)
const searchQuery = ref('')
const selectedProductId = ref('')
const totalRecords = ref(0)
const currentPage = ref(0)
const pageSize = ref(10)

const editDialogVisible = ref(false)
const editingItem = ref(null)
const newQuantity = ref(null)
const movementType = ref('IN')
const updateNotes = ref('')

const canDelete = ref(false)

let searchTimeout = null

const debounceSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 0
    loadInventory()
  }, 300)
}

const formatAttributes = (attributes) => {
  if (!attributes || typeof attributes !== 'object') return ''
  return Object.values(attributes).join(' • ')
}

const formatLastUpdated = (timestamp) => {
  return InventoryService.formatTimestamp(timestamp)
}

const loadInventory = async () => {
  if (!selectedProductId.value) {
    inventory.value = []
    totalRecords.value = 0
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const productData = products.value.find(p => p.id === parseInt(selectedProductId.value))
    if (!productData) {
      error.value = 'Product not found'
      inventory.value = []
      totalRecords.value = 0
      return
    }

    const variants = productData.variants || []
    let filtered = variants

    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      filtered = variants.filter(v => 
        v.sku.toLowerCase().includes(q) ||
        formatAttributes(v.attributes).toLowerCase().includes(q)
      )
    }

    inventory.value = filtered
    totalRecords.value = filtered.length
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

const loadProducts = async () => {
  try {
    const allProducts = await getProducts()
    products.value = allProducts
  } catch (err) {
    console.error('Failed to load products:', err)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load products',
      life: 3000,
    })
  }
}

const openEditDialog = (item) => {
  editingItem.value = { ...item }
  newQuantity.value = null
  movementType.value = 'IN'
  updateNotes.value = ''
  editDialogVisible.value = true
}

const saveStock = async () => {
  if (newQuantity.value === null || !editingItem.value) return

  isUpdating.value = true

  try {
    const finalQuantity = movementType.value === 'IN' 
      ? (editingItem.value.stock_quantity || 0) + newQuantity.value
      : Math.max(0, (editingItem.value.stock_quantity || 0) - newQuantity.value)

    await InventoryService.updateStock(
      editingItem.value.id,
      newQuantity.value,
      movementType.value,
      updateNotes.value
    )

    // Update the item in the inventory list immediately
    const itemIndex = inventory.value.findIndex(item => item.id === editingItem.value.id)
    if (itemIndex !== -1) {
      inventory.value[itemIndex].stock_quantity = finalQuantity
    }

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `Stock ${movementType.value === 'IN' ? 'added' : 'removed'}: ${editingItem.value.stock_quantity} → ${finalQuantity}`,
      life: 3000,
    })

    editDialogVisible.value = false
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
  if (confirm(`Delete inventory item for "${item.sku}"? This action cannot be undone.`)) {
    deleteInventory(item)
  }
}

const deleteInventory = async (item) => {
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
  loadProducts()
})
</script>
