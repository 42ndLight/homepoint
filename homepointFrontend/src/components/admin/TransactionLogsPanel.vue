<template>
  <div class="p-4">
    <!-- Header with Filters -->
    <div class="mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <!-- Start Date Filter -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">Start Date</label>
          <input
            v-model="filters.startDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <!-- End Date Filter -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">End Date</label>
          <input
            v-model="filters.endDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <!-- Status Filter -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">Status</label>
          <select
            v-model="filters.status"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        <!-- Search Box -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">Customer/Phone</label>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search customer..."
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            @input="debounceSearch"
          />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-2">
        <button
          @click="loadOrders"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
        >
          <i class="pi pi-search"></i>
          Apply Filters
        </button>
        <button
          @click="resetFilters"
          class="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition flex items-center gap-2"
        >
          <i class="pi pi-times"></i>
          Reset
        </button>
        <button
          @click="loadOrders"
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2 ml-auto"
          :disabled="isLoading"
        >
          <i class="pi pi-refresh" :class="{ 'animate-spin': isLoading }"></i>
          Refresh
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800 font-semibold">Error Loading Orders</p>
      <p class="text-red-700 text-sm mt-1">{{ error }}</p>
      <button
        @click="clearError"
        class="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
      >
        Dismiss
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && orders.length === 0" class="space-y-4">
      <div v-for="i in 5" :key="i" class="bg-gray-200 h-12 rounded animate-pulse"></div>
    </div>

    <!-- DataTable -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <DataTable
        :value="orders"
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
            <p>No orders found</p>
          </div>
        </template>

        <Column field="id" header="Order ID" :style="{ width: '100px' }" sortable>
          <template #body="{ data }">
            <span class="font-bold text-blue-600">#{{ data.id }}</span>
          </template>
        </Column>

        <Column field="customer_name" header="Customer" sortable>
          <template #body="{ data }">
            <div>
              <p class="font-medium text-gray-900">{{ data.customer_name || 'N/A' }}</p>
              <p class="text-xs text-gray-600">{{ data.customer_phone || 'No phone' }}</p>
            </div>
          </template>
        </Column>

        <Column field="formattedDate" header="Date" :style="{ width: '120px' }" sortable>
          <template #body="{ data }">
            <div class="text-sm">
              <p class="font-medium">{{ formatDate(data.created_at) }}</p>
              <p class="text-xs text-gray-600">{{ formatTime(data.created_at) }}</p>
            </div>
          </template>
        </Column>

        <Column field="total_amount" header="Amount" :style="{ width: '120px' }">
          <template #body="{ data }">
            <span class="font-bold text-green-600">{{ formatCurrency(data.total_amount) }}</span>
          </template>
        </Column>

        <Column field="payment_method" header="Payment" :style="{ width: '100px' }">
          <template #body="{ data }">
            <span class="text-sm px-2 py-1 rounded bg-gray-100 text-gray-800">
              {{ data.payment_method || 'N/A' }}
            </span>
          </template>
        </Column>

        <Column field="status" header="Status" :style="{ width: '120px' }">
          <template #body="{ data }">
            <span
              class="px-3 py-1 rounded text-xs font-semibold"
              :class="getStatusClass(data.status)"
            >
              {{ formatStatus(data.status) }}
            </span>
          </template>
        </Column>

        <Column header="Actions" :style="{ width: '200px' }">
          <template #body="{ data }">
            <div class="flex gap-2">
              <button
                @click="viewOrderDetails(data)"
                class="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition text-xs font-semibold flex items-center gap-1"
              >
                <i class="pi pi-eye"></i>
                View
              </button>
              <button
                @click="reprintReceipt(data)"
                class="px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 transition text-xs font-semibold flex items-center gap-1"
              >
                <i class="pi pi-print"></i>
                Print
              </button>
              <button
                @click="confirmDelete(data)"
                class="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition text-xs font-semibold flex items-center gap-1"
              >
                <i class="pi pi-trash"></i>
                Delete
              </button>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Order Details Dialog -->
    <Dialog
      v-model:visible="detailsDialogVisible"
      header="Order Details"
      :modal="true"
      :style="{ width: '500px' }"
    >
      <template v-if="selectedOrder">
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-gray-600 font-semibold">Order ID</p>
              <p class="font-bold text-lg text-blue-600">#{{ selectedOrder.id }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-600 font-semibold">Date</p>
              <p class="font-medium">{{ formatDate(selectedOrder.created_at) }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-xs text-gray-600 font-semibold mb-1">Customer</p>
              <p class="font-medium">{{ selectedOrder.customer_name || 'N/A' }}</p>
              <p class="text-sm text-gray-600">{{ selectedOrder.customer_phone || 'No phone' }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-600 font-semibold">Status</p>
              <span
                class="px-2 py-1 rounded text-xs font-semibold inline-block"
                :class="getStatusClass(selectedOrder.status)"
              >
                {{ formatStatus(selectedOrder.status) }}
              </span>
            </div>
            <div>
              <p class="text-xs text-gray-600 font-semibold">Payment</p>
              <p class="font-medium">{{ selectedOrder.payment_method || 'N/A' }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-xs text-gray-600 font-semibold mb-1">Total Amount</p>
              <p class="text-xl font-bold text-green-600">{{ formatCurrency(selectedOrder.total_amount) }}</p>
            </div>
          </div>

          <div v-if="selectedOrder.notes" class="bg-gray-50 p-3 rounded border border-gray-200">
            <p class="text-xs text-gray-600 font-semibold mb-1">Notes</p>
            <p class="text-sm text-gray-700">{{ selectedOrder.notes }}</p>
          </div>
        </div>
      </template>

      <template #footer>
        <button
          @click="detailsDialogVisible = false"
          class="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition"
        >
          Close
        </button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import TransactionService from '@/services/transactionService'

const router = useRouter()
const toast = useToast()

const orders = ref([])
const isLoading = ref(false)
const error = ref(null)
const totalRecords = ref(0)
const currentPage = ref(0)
const pageSize = ref(10)

const filters = ref({
  startDate: '',
  endDate: '',
  status: '',
})

const searchQuery = ref('')
const selectedOrder = ref(null)
const detailsDialogVisible = ref(false)

let searchTimeout = null

const debounceSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 0
    loadOrders()
  }, 300)
}

const loadOrders = async () => {
  isLoading.value = true
  error.value = null

  try {
    const params = {
      limit: pageSize.value,
      offset: currentPage.value * pageSize.value,
    }

    if (filters.value.startDate) params.start_date = filters.value.startDate
    if (filters.value.endDate) params.end_date = filters.value.endDate
    if (filters.value.status) params.status = filters.value.status
    if (searchQuery.value) params.search = searchQuery.value

    const response = await TransactionService.getOrders(params)

    if (Array.isArray(response)) {
      orders.value = response.map((order) => TransactionService.formatOrder(order))
      totalRecords.value = response.length
    } else if (response.results) {
      orders.value = response.results.map((order) => TransactionService.formatOrder(order))
      totalRecords.value = response.count || response.results.length
    } else {
      orders.value = []
      totalRecords.value = 0
    }
  } catch (err) {
    error.value = err.message || 'Failed to load orders'
    console.error('Orders load error:', err)
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

const resetFilters = () => {
  filters.value = {
    startDate: '',
    endDate: '',
    status: '',
  }
  searchQuery.value = ''
  currentPage.value = 0
  loadOrders()
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formatTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('en-KE', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numValue)
}

const formatStatus = (status) => {
  if (!status) return 'Unknown'
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
}

const getStatusClass = (status) => {
  return TransactionService.getStatusColor(status)
}

const viewOrderDetails = (order) => {
  selectedOrder.value = order
  detailsDialogVisible.value = true
}

const reprintReceipt = async (order) => {
  try {
    // Navigate to receipt view with order ID
    // This assumes you have a receipt view at /receipts/{id}
    await router.push({
      name: 'receipt', // Update this to your actual receipt route name
      params: { id: order.id },
    })
  } catch (err) {
    // If route doesn't exist, show a message
    toast.add({
      severity: 'info',
      summary: 'Info',
      detail: `Receipt for Order #${order.id} - Print functionality coming soon`,
      life: 3000,
    })
  }
}

const confirmDelete = (order) => {
  if (confirm(`Delete order #${order.id}? This action cannot be undone.`)) {
    deleteOrder(order)
  }
}

const deleteOrder = async (order) => {
  isLoading.value = true

  try {
    await TransactionService.deleteOrder(order.id)

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `Order #${order.id} deleted successfully`,
      life: 3000,
    })

    await loadOrders()
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.message || 'Failed to delete order',
      life: 3000,
    })
    console.error('Delete error:', err)
  } finally {
    isLoading.value = false
  }
}

const onPageChange = (event) => {
  currentPage.value = event.page
  pageSize.value = event.rows
  loadOrders()
}

const clearError = () => {
  error.value = null
}

onMounted(() => {
  loadOrders()
})
</script>
