<template>
  <div class="landing-page bg-white">
    <!-- Navigation Bar -->
    <nav class="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-blue-600 rounded-lg"></div>
          <h1 class="text-xl font-bold text-gray-900">Homepoint</h1>
        </div>
        <div class="flex items-center gap-4">
          <button
            @click="scrollToSection('products')"
            class="text-gray-700 hover:text-blue-600 font-medium text-sm"
          >
            Materials
          </button>
          <button
            @click="openQuoteModal"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm"
          >
            Quote
          </button>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <HeroSection @openModal="openQuoteModal" />

    <!-- Category Grid -->
    <div class="py-12 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-8">Shop by Category</h2>
        <CategoryGrid @selectCategory="selectCategory" />
      </div>
    </div>

    <!-- Product Grid -->
    <div ref="productsSection" class="py-12 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between mb-8">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">
              {{ selectedCategory ? `${selectedCategory.name}` : 'Featured Materials' }}
            </h2>
            <p class="text-gray-600 text-sm mt-2">
              Browse our selection and request quotes for bulk orders
            </p>
          </div>
          <button
            v-if="selectedCategory"
            @click="selectedCategory = null"
            class="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Clear Filter
          </button>
        </div>
        <ProductGrid :categoryId="selectedCategory?.id" @addToQuote="addProductToQuote" />
      </div>
    </div>

    <!-- Trust Section -->
    <TrustSection />

    <!-- Bulk Quote CTA Section -->
    <BulkQuoteCTA @openModal="openQuoteModal" />

    <!-- Footer -->
    <Footer />

    <!-- Quote Request Modal -->
    <QuoteRequestModal
      :isOpen="showQuoteModal"
      :selectedProducts="quoteProducts"
      @close="closeQuoteModal"
      @submit="submitQuote"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { syncProducts } from '@/services/dbService'
import { useQuote } from '@/composables/useLanding'
import HeroSection from '@/components/landing/HeroSection.vue'
import CategoryGrid from '@/components/landing/CategoryGrid.vue'
import ProductGrid from '@/components/landing/ProductGrid.vue'
import TrustSection from '@/components/landing/TrustSection.vue'
import BulkQuoteCTA from '@/components/landing/BulkQuoteCTA.vue'
import QuoteRequestModal from '@/components/landing/QuoteRequestModal.vue'
import Footer from '@/components/landing/Footer.vue'

const showQuoteModal = ref(false)
const selectedCategory = ref(null)
const quoteProducts = ref([])
const productsSection = ref(null)

const { submitQuote: submitQuoteToBackend } = useQuote()

// Sync products on component mount
onMounted(async () => {
  try {
    await syncProducts()
    console.log('Products synced successfully')
  } catch (error) {
    console.error('Failed to sync products:', error)
  }
})

const openQuoteModal = () => {
  showQuoteModal.value = true
}

const closeQuoteModal = () => {
  showQuoteModal.value = false
}

const selectCategory = (category) => {
  selectedCategory.value = category
  scrollToSection('products')
}

const addProductToQuote = (product) => {
  // Add product variants to quote with default quantity 1
  if (product.variants && product.variants.length > 0) {
    product.variants.forEach((variant) => {
      const existing = quoteProducts.value.find((p) => p.id === variant.id)
      if (existing) {
        existing.quantity += 1
      } else {
        quoteProducts.value.push({
          id: variant.id,
          name: `${product.name}${variant.attributes ? ' • ' + Object.values(variant.attributes).join(' • ') : ''}`,
          sku: variant.sku,
          price: variant.price,
          quantity: 1,
        })
      }
    })
  } else {
    // Fallback to product itself if no variants
    const existing = quoteProducts.value.find((p) => p.id === product.id)
    if (existing) {
      existing.quantity += 1
    } else {
      quoteProducts.value.push({
        id: product.id,
        name: product.name,
        price: product.base_price,
        quantity: 1,
      })
    }
  }
  openQuoteModal()
}

const scrollToSection = (sectionRef) => {
  if (sectionRef === 'products' && productsSection.value) {
    productsSection.value.scrollIntoView({ behavior: 'smooth' })
  }
}

const submitQuote = async (quoteData) => {
  try {
    await submitQuoteToBackend(quoteData)
    closeQuoteModal()
    quoteProducts.value = []
    // Show success message (could add a toast here)
    console.log('Quote submitted successfully')
  } catch (error) {
    console.error('Failed to submit quote:', error)
    // Show error message (could add a toast here)
  }
}
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
}
</style>
