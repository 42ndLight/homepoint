<template>
  <div class="bg-white rounded-lg shadow p-6 mb-6">
    <h2 class="text-xl font-bold text-gray-800 mb-4">Daily Revenue Trend</h2>
    <div class="w-full h-80">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { defineProps, ref, watch, onMounted } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps({
  dailyData: {
    type: Array,
    default: () => [],
  },
})

const chartCanvas = ref(null)
let chartInstance = null

const formatChartData = () => {
  if (!props.dailyData || props.dailyData.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = props.dailyData.map((item) => item.date)
  const revenues = props.dailyData.map((item) => parseFloat(item.total_sales) || 0)
  const mpesaSales = props.dailyData.map((item) => parseFloat(item.mpesa_sales) || 0)
  const cashSales = props.dailyData.map((item) => parseFloat(item.cash_sales) || 0)

  return {
    labels,
    datasets: [
      {
        label: 'Total Revenue',
        data: revenues,
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#2563eb',
        pointBorderColor: '#1e40af',
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'M-Pesa Sales',
        data: mpesaSales,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.05)',
        borderWidth: 1,
        tension: 0.4,
        fill: false,
        pointBackgroundColor: '#f59e0b',
        pointRadius: 2,
        borderDash: [5, 5],
      },
      {
        label: 'Cash Sales',
        data: cashSales,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.05)',
        borderWidth: 1,
        tension: 0.4,
        fill: false,
        pointBackgroundColor: '#10b981',
        pointRadius: 2,
        borderDash: [5, 5],
      },
    ],
  }
}

const initChart = () => {
  if (chartCanvas.value) {
    // Destroy existing chart if it exists
    if (chartInstance) {
      chartInstance.destroy()
    }

    const ctx = chartCanvas.value.getContext('2d')
    const chartData = formatChartData()

    chartInstance = new Chart(ctx, {
      type: 'line',
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              boxWidth: 12,
              padding: 15,
              font: {
                size: 12,
              },
            },
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: (context) => {
                let label = context.dataset.label || ''
                if (label) {
                  label += ': '
                }
                const value = context.parsed.y
                label += new Intl.NumberFormat('en-KE', {
                  style: 'currency',
                  currency: 'KES',
                  minimumFractionDigits: 0,
                }).format(value)
                return label
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => {
                return new Intl.NumberFormat('en-KE', {
                  notation: 'compact',
                  compactDisplay: 'short',
                }).format(value)
              },
            },
            title: {
              display: true,
              text: 'Revenue (KES)',
            },
          },
          x: {
            title: {
              display: true,
              text: 'Date',
            },
          },
        },
      },
    })
  }
}

watch(() => props.dailyData, () => {
  initChart()
})

onMounted(() => {
  initChart()
})
</script>
