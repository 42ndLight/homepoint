<template>
  <div class="p-4">
    <!-- Header with Filters -->
    <div class="mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <!-- Start Date Filter -->
        <div>
          <label for="start-date" class="block text-sm font-semibold text-gray-700 mb-2">Start Date</label>
          <input
            id="start-date"
            v-model="filters.startDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <!-- End Date Filter -->
        <div>
          <label for="end-date" class="block text-sm font-semibold text-gray-700 mb-2">End Date</label>
          <input
            id="end-date"
            v-model="filters.endDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <!-- Transaction Type Filter -->
        <div>
          <label for="trans-type" class="block text-sm font-semibold text-gray-700 mb-2">Transaction Type</label>
          <select
            id="trans-type"
            v-model="filters.type"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Types</option>
            <option value="SALES">Sales Payment</option>
            <option value="EXPENSE">Expense Payment</option>
            <option value="PURCHASE">Purchase Payment</option>
            <option value="DEPOSIT">Cash Deposit</option>
            <option value="WITHDRAWAL">Cash Withdrawal</option>
            <option value="REFUND">Refund</option>
          </select>
        </div>

        <!-- Search Box -->
        <div>
          <label for="search-logs" class="block text-sm font-semibold text-gray-700 mb-2">Reference / Notes</label>
          <input
            id="search-logs"
            v-model="searchQuery"
            type="text"
            placeholder="Search transactions..."
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            @input="debounceSearch"
          />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-2">
        <button
          @click="loadTransactions"
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
          @click="loadTransactions"
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
      <p class="text-red-800 font-semibold">Error Loading Transactions</p>
      <p class="text-red-700 text-sm mt-1">{{ error }}</p>
      <button
        @click="clearError"
        class="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
      >
        Dismiss
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && transactions.length === 0" class="space-y-4">
      <div v-for="i in 5" :key="i" class="bg-gray-200 h-12 rounded animate-pulse"></div>
    </div>

    <!-- DataTable -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <DataTable
        :value="transactions"
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
            <p>No transactions found</p>
          </div>
        </template>

        <Column field="id" header="ID" :style="{ width: '80px' }" sortable>
          <template #body="{ data }">
            <span class="text-gray-500">#{{ data.id }}</span>
          </template>
        </Column>

        <Column field="transaction_type_display" header="Type" sortable>
          <template #body="{ data }">
             <span class="font-medium">{{ data.transaction_type_display }}</span>
          </template>
        </Column>

        <Column field="movement_type" header="Mvmt" :style="{ width: '100px' }">
          <template #body="{ data }">
            <span :class="getMovementClass(data.movement_type)">
              {{ data.movement_type === 'IN' ? '↑ IN' : '↓ OUT' }}
            </span>
          </template>
        </Column>

        <Column field="formattedDate" header="Date" :style="{ width: '120px' }" sortable>
          <template #body="{ data }">
            <div class="text-sm">
              <p class="font-medium">{{ data.formattedDate }}</p>
              <p class="text-xs text-gray-600">{{ data.formattedTime }}</p>
            </div>
          </template>
        </Column>

        <Column field="amount" header="Amount" :style="{ width: '120px' }">
          <template #body="{ data }">
            <span class="font-bold" :class="data.movement_type === 'IN' ? 'text-green-600' : 'text-red-600'">
              {{ data.formattedAmount }}
            </span>
          </template>
        </Column>

        <Column field="status" header="Status" :style="{ width: '160px' }">
          <template #body="{ data }">
            <Tag :value="formatStatus(data)" :severity="getStatusSeverity(data)" />
          </template>
        </Column>

        <Column field="reference_id" header="Reference">
          <template #body="{ data }">
            <span class="text-sm font-mono">{{ data.reference_id || '-' }}</span>
          </template>
        </Column>

        <Column header="Actions" :style="{ width: '180px' }">
          <template #body="{ data }">
            <div class="flex gap-2">
              <button
                @click="viewDetails(data)"
                class="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition text-xs font-semibold flex items-center gap-1"
              >
                <i class="pi pi-eye"></i>
                Details
              </button>
              <button
                v-if="data.order_id"
                @click="reprintReceipt(data)"
                class="px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 transition text-xs font-semibold flex items-center gap-1"
              >
                <i class="pi pi-print"></i>
                Receipt
              </button>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Transaction Details Dialog -->
    <Dialog
      v-model:visible="detailsDialogVisible"
      header="Transaction Details"
      :modal="true"
      :style="{ width: '500px' }"
    >
      <template v-if="selectedTransaction">
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-gray-600 font-semibold">Transaction ID</p>
              <p class="font-bold text-lg text-blue-600">#{{ selectedTransaction.id }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-600 font-semibold">Date & Time</p>
              <p class="font-medium">{{ selectedTransaction.formattedDate }} {{ selectedTransaction.formattedTime }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-600 font-semibold">Type</p>
              <p class="font-medium">{{ selectedTransaction.transaction_type_display }}</p>
            </div>
             <div>
              <p class="text-xs text-gray-600 font-semibold">Movement</p>
              <p :class="getMovementClass(selectedTransaction.movement_type)">
                {{ selectedTransaction.movement_type_display }}
              </p>
            </div>
            <div class="col-span-2">
              <p class="text-xs text-gray-600 font-semibold mb-1">Amount</p>
              <p class="text-xl font-bold" :class="selectedTransaction.movement_type === 'IN' ? 'text-green-600' : 'text-red-600'">
                {{ selectedTransaction.formattedAmount }}
              </p>
            </div>
             <div v-if="selectedTransaction.balance_after !== undefined">
              <p class="text-xs text-gray-600 font-semibold">Balance After</p>
              <p class="font-medium">{{ formatCurrency(selectedTransaction.balance_after) }}</p>
            </div>
            <div v-if="selectedTransaction.reference_id">
              <p class="text-xs text-gray-600 font-semibold">Reference ID</p>
              <p class="font-medium font-mono">{{ selectedTransaction.reference_id }}</p>
            </div>
             <div v-if="selectedTransaction.order_id" class="col-span-2">
              <p class="text-xs text-gray-600 font-semibold">Linked Order</p>
              <p class="font-bold text-blue-600">Order #{{ selectedTransaction.order_id }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-600 font-semibold">Status</p>
              <Tag :value="formatStatus(selectedTransaction)" :severity="getStatusSeverity(selectedTransaction)" />
            </div>
          </div>

          <div v-if="selectedTransaction.notes" class="bg-gray-50 p-3 rounded border border-gray-200">
            <p class="text-xs text-gray-600 font-semibold mb-1">Notes</p>
            <p class="text-sm text-gray-700">{{ selectedTransaction.notes }}</p>
          </div>
        </div>
      </template>

      <template #footer>
        <div class="flex justify-between w-full">
           <button
            v-if="selectedTransaction?.order_id"
            @click="reprintReceipt(selectedTransaction)"
            class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition flex items-center gap-2"
          >
            <i class="pi pi-print"></i>
            Print Receipt
          </button>
          <div v-else></div>
          <button
            @click="detailsDialogVisible = false"
            class="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition"
          >
            Close
          </button>
        </div>
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
import Tag from 'primevue/tag'
import TransactionService from '@/services/transactionService'

const router = useRouter()
const toast = useToast()

const transactions = ref([])
const isLoading = ref(false)
const error = ref(null)
const totalRecords = ref(0)
const currentPage = ref(0)
const pageSize = ref(10)

const filters = ref({
  startDate: '',
  endDate: '',
  type: '',
})

const searchQuery = ref('')
const selectedTransaction = ref(null)
const detailsDialogVisible = ref(false)

let searchTimeout = null

const debounceSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 0
    loadTransactions()
  }, 300)
}

const loadTransactions = async () => {
  isLoading.value = true
  error.value = null

  try {
    const params = {
      limit: pageSize.value,
      offset: currentPage.value * pageSize.value,
    }

    if (filters.value.startDate) params.start_date = filters.value.startDate
    if (filters.value.endDate) params.end_date = filters.value.endDate
    if (filters.value.type) params.transaction_type = filters.value.type
    if (searchQuery.value) params.search = searchQuery.value

    const response = await TransactionService.getTransactions(params)

    if (Array.isArray(response)) {
      transactions.value = response.map(t => TransactionService.formatTransaction(t))
      totalRecords.value = response.length
    } else if (response.results) {
      transactions.value = response.results.map(t => TransactionService.formatTransaction(t))
      totalRecords.value = response.count || response.results.length
    } else {
      transactions.value = []
      totalRecords.value = 0
    }
  } catch (err) {
    error.value = err.message || 'Failed to load transactions'
    console.error('Transactions load error:', err)
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
    type: '',
  }
  searchQuery.value = ''
  currentPage.value = 0
  loadTransactions()
}

const formatCurrency = (value) => {
  const numValue = Number.parseFloat(value) || 0
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numValue)
}

const getMovementClass = (type) => {
  return TransactionService.getMovementColor(type)
}

const formatStatus = (data) => {
  // 1. Check M-Pesa / Transaction level status first
  if (data.status) {
    const s = data.status.toLowerCase()
    if (s === 'pending') return 'Pending Payment'
    if (s === 'failed') return 'Payment Failed'
    if (s === 'cancelled') return 'Payment Cancelled'
    if (s === 'success') return 'Payment Success'
  }
  
  // 2. Check Order level status
  if (data.order_status) {
    const s = data.order_status.toLowerCase()
    const map = { 
      pending: 'Order Pending', 
      paid: 'Order Paid', 
      delivered: 'Delivered', 
      cancelled: 'Cancelled' 
    }
    return map[s] || data.order_status
  }
  
  // 3. Default for finalized transactions (Cash, Expenses, etc)
  return 'Completed'
}

const getStatusSeverity = (data) => {
  // 1. Transaction level severity
  if (data.status) {
    const s = data.status.toLowerCase()
    if (s === 'pending') return 'warn'
    if (s === 'failed' || s === 'cancelled') return 'danger'
    if (s === 'success') return 'success'
  }

  // 2. Order level severity
  if (data.order_status) {
    const s = data.order_status.toLowerCase()
    const map = { 
      pending: 'warn', 
      paid: 'success', 
      delivered: 'success', 
      cancelled: 'danger' 
    }
    return map[s] || 'info'
  }

  return 'success'
}

const viewDetails = (transaction) => {
  selectedTransaction.value = transaction
  detailsDialogVisible.value = true
}

const reprintReceipt = (transaction) => {
  if (!transaction.order_id) return
  
  try {
    const url = router.resolve({
      name: 'receipt',
      params: { orderId: transaction.order_id },
      query: { print: 'true' }
    }).href
    
    window.open(url, '_blank')
  } catch (err) {
    console.error('Print navigation error:', err)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Could not open receipt for printing',
      life: 3000,
    })
  }
}

const onPageChange = (event) => {
  currentPage.value = event.page
  pageSize.value = event.rows
  loadTransactions()
}

const clearError = () => {
  error.value = null
}

onMounted(() => {
  loadTransactions()
})
</script>
