<template>
  <div class="bulk-quote-cta py-12 md:py-16 bg-gradient-to-r from-blue-50 to-blue-100 border-t border-blue-200">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
        💼 Need Materials in Bulk?
      </h2>
      <p class="text-lg text-gray-700 mb-8 max-w-2xl mx-auto">
        Get instant custom quotes from our team. The more you order, the better your pricing.
        <br />
        <span class="text-sm text-gray-600 mt-2 block">Average response time: 15 minutes during business hours</span>
      </p>

      <!-- Contact Options Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <!-- Email -->
        <a href="mailto:quotes@homepoint.ke" class="p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-gray-200">
          <div class="text-2xl mb-2">📧</div>
          <div class="text-sm font-semibold text-gray-900">Email Quote</div>
          <div class="text-xs text-gray-600">quotes@homepoint.ke</div>
        </a>

        <!-- WhatsApp -->
        <a href="https://wa.me/254712345678?text=Hi%20Homepoint%2C%20I%20need%20a%20bulk%20quote" target="_blank" rel="noopener noreferrer" class="p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-green-200 bg-green-50">
          <div class="text-2xl mb-2">💬</div>
          <div class="text-sm font-semibold text-gray-900">WhatsApp</div>
          <div class="text-xs text-gray-600">+254 712 345 678</div>
        </a>

        <!-- Phone -->
        <a href="tel:+254712345678" class="p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-gray-200">
          <div class="text-2xl mb-2">📞</div>
          <div class="text-sm font-semibold text-gray-900">Call Us</div>
          <div class="text-xs text-gray-600">+254 712 345 678</div>
        </a>
      </div>

      <!-- Primary CTA -->
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          @click="$emit('openModal')"
          class="px-8 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105"
        >
          Get Quote Now
        </button>
        <a
          href="https://wa.me/254712345678?text=Hi%20Homepoint%2C%20I%20would%20like%20a%20bulk%20quote"
          target="_blank"
          rel="noopener noreferrer"
          class="px-8 py-3 bg-white text-blue-600 font-bold rounded-lg hover:bg-gray-50 transition-all duration-200 border-2 border-blue-600 flex items-center justify-center gap-2"
        >
          <span>💬</span>
          Chat on WhatsApp
        </a>
      </div>

      <!-- Secondary text -->
      <p class="mt-8 text-sm text-gray-600">
        ⏰ Open 6am - 6pm daily | 📍 Serving all Nairobi & surrounding counties
      </p>
    </div>
  </div>
</template>

<script setup>
defineEmits(['openModal'])
</script>

<style scoped>
.bulk-quote-cta {
  position: relative;
  overflow: hidden;
}
</style>
