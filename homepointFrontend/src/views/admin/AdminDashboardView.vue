<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-800">Admin Dashboard</h1>
      <p class="text-gray-600 mt-1">Manage store operations, sales, staff, and inventory</p>
    </div>

    <!-- Tabs Container -->
    <Tabs value="Sales & Reports">
      <TabList>
              <Tab value="Sales & Reports">Sales & Reports</Tab>
              <Tab value="Transaction Logs">Transaction Logs</Tab>
              <Tab value="Inventory Control">Inventory Control</Tab>
              <Tab value="Store Details">Store Details</Tab>
          </TabList>
      <!-- Sales & Reporting Tab -->
      <TabPanels>
      <TabPanel value="Sales & Reports" leftIcon="pi pi-chart-bar">
        <div class="p-4">
          <!-- Date Range Filter -->
          <DateRangeFilter @filter-change="handleFilterChange" />

          <!-- Loading & Error States -->
          <div v-if="isLoading" class="bg-white rounded-lg shadow p-8 text-center">
            <div class="inline-block">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
            <p class="text-gray-600 mt-4">Loading analytics data...</p>
          </div>

          <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p class="text-red-800 font-semibold">Error Loading Data</p>
            <p class="text-red-700 text-sm mt-1">{{ error }}</p>
            <button
              @click="loadAnalytics"
              class="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
            >
              Retry
            </button>
          </div>

          <div v-else>
            <!-- Summary Cards -->
            <SalesSummary :summary="analyticsData.summary" />

            <!-- Charts Section -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <!-- Revenue Chart -->
              <SalesChart :daily-data="analyticsData.daily_revenue" />

              <!-- Top Products Chart -->
              <ProductSalesChart :top-products="analyticsData.top_products" />
            </div>

            <!-- Top Products Table (optional detailed view) -->
            <div v-if="analyticsData.top_products.length > 0" class="bg-white rounded-lg shadow p-6 mt-6">
              <h2 class="text-xl font-bold text-gray-800 mb-4">Top Products Detailed</h2>
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b border-gray-200">
                      <th class="text-left py-3 px-4 font-semibold text-gray-700">Rank</th>
                      <th class="text-left py-3 px-4 font-semibold text-gray-700">Product Name</th>
                      <th class="text-left py-3 px-4 font-semibold text-gray-700">SKU</th>
                      <th class="text-right py-3 px-4 font-semibold text-gray-700">Units Sold</th>
                      <th class="text-right py-3 px-4 font-semibold text-gray-700">Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(product, index) in analyticsData.top_products"
                      :key="index"
                      class="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td class="py-3 px-4">
                        <span
                          class="inline-block bg-blue-100 text-blue-800 rounded-full w-6 h-6 text-center font-semibold text-xs"
                        >
                          {{ index + 1 }}
                        </span>
                      </td>
                      <td class="py-3 px-4">{{ product.product_name }}</td>
                      <td class="py-3 px-4 text-gray-600">{{ product.sku }}</td>
                      <td class="py-3 px-4 text-right font-semibold">{{ product.quantity }}</td>
                      <td class="py-3 px-4 text-right font-semibold text-green-600">
                        {{ formatCurrency(product.revenue) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </TabPanel>

      <!-- Staff Management Tab -->
      <TabPanel value="Transaction Logs" leftIcon="pi pi-receipt">
        <TransactionLogsPanel />
      </TabPanel>

      <!-- Inventory Control Tab -->
      <TabPanel value="Inventory Control" leftIcon="pi pi-box">
        <InventoryControlPanel />
      </TabPanel>

      <!-- Store Details Tab -->
      <TabPanel value="Store Details" leftIcon="pi pi-cog">
        <div class="p-4">
          <div class="bg-amber-50 border-l-4 border-amber-600 p-4 rounded">
            <p class="text-amber-800 font-semibold">⚙️ Store Details & Settings</p>
            <p class="text-amber-700 text-sm mt-2">
              Configure store information and system settings. Features coming soon:
            </p>
            <ul class="text-amber-700 text-sm mt-2 ml-4 list-disc">
              <li>Store information (name, address, phone)</li>
              <li>Tax configuration (TIN, VAT rates)</li>
              <li>Currency and locale settings</li>
              <li>System preferences and defaults</li>
              <li>Backup and data management</li>
            </ul>
          </div>
        </div>
      </TabPanel>
    </TabPanels>
    </Tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import DateRangeFilter from '@/components/admin/DateRangeFilter.vue'
import SalesSummary from '@/components/admin/SalesSummary.vue'
import SalesChart from '@/components/admin/SalesChart.vue'
import ProductSalesChart from '@/components/admin/ProductSalesChart.vue'
import AnalyticsService from '@/services/analyticsService'
import InventoryControlPanel from '@/components/admin/InventoryControlPanel.vue'
import TransactionLogsPanel from '@/components/admin/TransactionLogsPanel.vue'

const isLoading = ref(false)
const error = ref(null)

const analyticsData = reactive({
  daily_revenue: [],
  top_products: [],
  summary: {
    total_revenue: '0',
    total_orders: 0,
    avg_order_value: '0',
    total_mpesa: '0',
    total_cash: '0',
  },
})

const currentDateRange = ref({
  startDate: '',
  endDate: '',
})

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numValue)
}

const loadAnalytics = async () => {
  if (!currentDateRange.value.startDate || !currentDateRange.value.endDate) {
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const data = await AnalyticsService.getSalesData(
      currentDateRange.value.startDate,
      currentDateRange.value.endDate,
      10
    )

    if (data.success) {
      analyticsData.daily_revenue = data.daily_revenue || []
      analyticsData.top_products = data.top_products || []
      analyticsData.summary = data.summary || {
        total_revenue: '0',
        total_orders: 0,
        average_order_value: '0',
        total_mpesa: '0',
        total_cash: '0',
      }
    } else {
      error.value = data.error || 'Failed to load analytics data'
    }
  } catch (err) {
    error.value = err.message || 'An error occurred while loading analytics'
    console.error('Analytics error:', err)
  } finally {
    isLoading.value = false
  }
}

const handleFilterChange = (dateRange) => {
  currentDateRange.value = dateRange
  loadAnalytics()
}

onMounted(() => {
  // Initial load will be triggered by DateRangeFilter's default initialization
})
</script>
