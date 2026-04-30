<template>
  <div v-if="isOpen" class="modal-overlay fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="modal-content bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
        <h2 class="text-xl font-bold text-gray-900">Request a Quote</h2>
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
        >
          ×
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <!-- Contact Information -->
        <div>
          <label for="quote-name" class="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
          <input
            id="quote-name"
            v-model="form.name"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            placeholder="Your name"
          />
        </div>

        <div>
          <label for="quote-email" class="block text-sm font-medium text-gray-700 mb-1">Email *</label>
          <input
            id="quote-email"
            v-model="form.email"
            type="email"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            placeholder="your@email.com"
          />
        </div>

        <div>
          <label for="quote-phone" class="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
          <input
            id="quote-phone"
            v-model="form.phone"
            type="tel"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            placeholder="+254 712 345 678"
          />
        </div>

        <!-- Selected Products (if any) -->
        <div v-if="selectedProducts.length > 0" class="border-t pt-4">
          <span class="block text-sm font-medium text-gray-700 mb-3">Selected Materials</span>
          <div class="space-y-2 bg-gray-50 p-3 rounded-lg max-h-40 overflow-y-auto">
            <div v-for="product in selectedProducts" :key="product.id" class="flex items-center justify-between text-sm">
              <span class="text-gray-700">{{ product.name }}</span>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  @click="decreaseQuantity(product.id)"
                  class="px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded"
                >
                  −
                </button>
                <span class="w-8 text-center font-medium">{{ product.quantity }}</span>
                <button
                  type="button"
                  @click="increaseQuantity(product.id)"
                  class="px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded"
                >
                  +
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Message -->
        <div>
          <label for="quote-message" class="block text-sm font-medium text-gray-700 mb-1">Project Details</label>
          <textarea
            id="quote-message"
            v-model="form.message"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
            placeholder="Describe your project or any specific requirements..."
          ></textarea>
        </div>

        <!-- Submission -->
        <div class="pt-4 border-t space-y-3">
          <button
            type="submit"
            class="w-full px-4 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Send Quote Request
          </button>
          <a
            :href="`https://wa.me/254712345678?text=Hi%20Homepoint%2C%20I%20would%20like%20a%20quote%20for%20my%20project.%20Name%3A%20${form.name}%20Phone%3A%20${form.phone}`"
            target="_blank"
            rel="noopener noreferrer"
            class="block w-full px-4 py-2 bg-green-500 text-white font-bold rounded-lg hover:bg-green-600 transition-colors text-center"
          >
            Send via WhatsApp
          </a>
        </div>

        <p class="text-xs text-gray-500 text-center">
          We'll get back to you within 2 hours during business hours
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  selectedProducts: {
    type: Array,
    default: () => [],
  },
})

const form = ref({
  name: '',
  email: '',
  phone: '',
  message: '',
})

const localProducts = computed({
  get: () => props.selectedProducts,
  set: (value) => {
    // Products managed by parent
  },
})

const increaseQuantity = (productId) => {
  const product = localProducts.value.find((p) => p.id === productId)
  if (product) {
    product.quantity += 1
  }
}

const decreaseQuantity = (productId) => {
  const product = localProducts.value.find((p) => p.id === productId)
  if (product && product.quantity > 1) {
    product.quantity -= 1
  }
}

const handleSubmit = async () => {
  const quoteData = {
    ...form.value,
    products: localProducts.value.map((p) => ({
      id: p.id,
      quantity: p.quantity,
    })),
  }

  try {
    // Submit to backend
    // TODO: Implement API call to POST /api/quotes/
    console.log('Quote data:', quoteData)

    // Emit submit event
    emit('submit', quoteData)

    // Reset form
    form.value = { name: '', email: '', phone: '', message: '' }
  } catch (error) {
    console.error('Failed to submit quote:', error)
  }
}

const emit = defineEmits(['close', 'submit'])
</script>

<style scoped>
.modal-overlay {
  backdrop-filter: blur(2px);
}

.modal-content {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
