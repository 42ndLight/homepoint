<template>
  <div class="flex flex-col gap-4 mb-6 bg-white p-4 rounded-lg shadow">
    <div class="flex flex-wrap gap-3 items-center">
      <span class="font-semibold text-gray-700">Date Range:</span>

      <!-- Quick Filter Buttons -->
      <button
        v-for="option in quickOptions"
        :key="option.label"
        @click="applyQuickFilter(option)"
        :class="{
          'bg-blue-600 text-white': isActiveFilter(option),
          'bg-gray-200 text-gray-700 hover:bg-gray-300': !isActiveFilter(option),
        }"
        class="px-3 py-1 rounded text-sm font-medium transition"
      >
        {{ option.label }}
      </button>
    </div>

    <!-- Custom Date Range -->
    <div class="flex flex-wrap gap-4 items-end">
      <div class="flex flex-col">
        <label for="custom-start-date" class="text-sm font-medium text-gray-700 mb-1">Start Date</label>
        <input
          id="custom-start-date"
          v-model="customStartDate"
          type="date"
          class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div class="flex flex-col">
        <label for="custom-end-date" class="text-sm font-medium text-gray-700 mb-1">End Date</label>
        <input
          id="custom-end-date"
          v-model="customEndDate"
          type="date"
          class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        @click="applyCustomDateRange"
        class="px-4 py-2 bg-green-600 text-white rounded font-medium hover:bg-green-700 transition"
      >
        Apply
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AnalyticsService from '@/services/analyticsService'

const emit = defineEmits(['filter-change'])

const customStartDate = ref('')
const customEndDate = ref('')

const quickOptions = [
  { label: 'Last 7 Days', days: 7 },
  { label: 'Last 30 Days', days: 30 },
  { label: 'This Month', type: 'currentMonth' },
  { label: 'Previous Month', type: 'previousMonth' },
]

const currentFilter = ref(null)

const isActiveFilter = (option) => {
  return currentFilter.value === option.label
}

const applyQuickFilter = (option) => {
  currentFilter.value = option.label

  let dateRange
  if (option.type === 'currentMonth') {
    dateRange = AnalyticsService.getDateRangeCurrentMonth()
  } else if (option.type === 'previousMonth') {
    dateRange = AnalyticsService.getDateRangePreviousMonth()
  } else {
    dateRange = AnalyticsService.getDateRangeLastDays(option.days)
  }

  customStartDate.value = dateRange.startDate
  customEndDate.value = dateRange.endDate

  emit('filter-change', dateRange)
}

const applyCustomDateRange = () => {
  if (!customStartDate.value || !customEndDate.value) {
    alert('Please select both start and end dates')
    return
  }

  if (customStartDate.value > customEndDate.value) {
    alert('Start date must be before end date')
    return
  }

  currentFilter.value = 'Custom'

  emit('filter-change', {
    startDate: customStartDate.value,
    endDate: customEndDate.value,
  })
}

// Initialize with last 7 days on mount
onMounted(() => {
  const dateRange = AnalyticsService.getDateRangeLastDays(7)
  customStartDate.value = dateRange.startDate
  customEndDate.value = dateRange.endDate
  currentFilter.value = 'Last 7 Days'
  emit('filter-change', dateRange)
})
</script>
