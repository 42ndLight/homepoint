<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <!-- Total Revenue Card -->
    <div class="bg-white rounded-lg shadow p-6 border-l-4 border-blue-600">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-gray-600 text-sm font-medium">Total Revenue</p>
          <p class="text-2xl font-bold text-blue-600 mt-2">
            {{ formatCurrency(summary.total_revenue) }}
          </p>
        </div>
        <div class="text-4xl text-blue-100">💰</div>
      </div>
    </div>

    <!-- Total Orders Card -->
    <div class="bg-white rounded-lg shadow p-6 border-l-4 border-green-600">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-gray-600 text-sm font-medium">Total Orders</p>
          <p class="text-2xl font-bold text-green-600 mt-2">{{ summary.total_orders }}</p>
        </div>
        <div class="text-4xl text-green-100">📦</div>
      </div>
    </div>

    <!-- Average Order Value Card -->
    <div class="bg-white rounded-lg shadow p-6 border-l-4 border-purple-600">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-gray-600 text-sm font-medium">Avg Order Value</p>
          <p class="text-2xl font-bold text-purple-600 mt-2">
            {{ formatCurrency(summary.average_order_value) }}
          </p>
        </div>
        <div class="text-4xl text-purple-100">📊</div>
      </div>
    </div>

    <!-- Payment Methods Card -->
    <div class="bg-white rounded-lg shadow p-6 border-l-4 border-orange-600">
      <div>
        <p class="text-gray-600 text-sm font-medium mb-3">Payment Breakdown</p>
        <div class="space-y-2">
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-600">M-Pesa:</span>
            <span class="font-semibold text-orange-600">{{ formatCurrency(summary.total_mpesa) }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-600">Cash:</span>
            <span class="font-semibold text-orange-600">{{ formatCurrency(summary.total_cash) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  summary: {
    type: Object,
    default: () => ({
      total_revenue: '0',
      total_orders: 0,
      average_order_value: '0',
      total_mpesa: '0',
      total_cash: '0',
    }),
  },
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
</script>
