<template>
  <div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-4">Top 10 Products</h2>
    <div class="w-full h-80">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { defineProps, ref, watch, onMounted } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps({
  topProducts: {
    type: Array,
    default: () => [],
  },
})

const chartCanvas = ref(null)
let chartInstance = null

const formatChartData = () => {
  if (!props.topProducts || props.topProducts.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const labels = props.topProducts.map((product) => product.product_name)
  const quantities = props.topProducts.map((product) => product.quantity || 0)
  const revenues = props.topProducts.map((product) => parseFloat(product.revenue) || 0)

  return {
    labels,
    datasets: [
      {
        label: 'Units Sold',
        data: quantities,
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderColor: '#1e40af',
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        label: 'Revenue (KES)',
        data: revenues,
        backgroundColor: 'rgba(34, 197, 94, 0.7)',
        borderColor: '#15803d',
        borderWidth: 1,
        yAxisID: 'y1',
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
      type: 'bar',
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
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
            callbacks: {
              label: (context) => {
                let label = context.dataset.label || ''
                if (label) {
                  label += ': '
                }
                const value = context.parsed[context.dataset.yAxisID === 'y' ? 'y' : 'y']

                if (context.dataset.yAxisID === 'y1') {
                  label += new Intl.NumberFormat('en-KE', {
                    style: 'currency',
                    currency: 'KES',
                    minimumFractionDigits: 0,
                  }).format(value)
                } else {
                  label += value
                }
                return label
              },
            },
          },
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            beginAtZero: true,
            title: {
              display: true,
              text: 'Units Sold',
            },
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
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
            grid: {
              drawOnChartArea: false,
            },
          },
          x: {
            stacked: false,
          },
        },
      },
    })
  }
}

watch(() => props.topProducts, () => {
  initChart()
})

onMounted(() => {
  initChart()
})
</script>
