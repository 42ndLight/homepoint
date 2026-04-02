<template>
  <div class="trust-section py-12 md:py-16 bg-white border-t border-gray-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h2 class="text-2xl font-bold text-gray-900 text-center mb-12">Why Choose Homepoint?</h2>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <!-- Trust Factor 1: Fast Delivery -->
        <div class="flex flex-col items-center text-center">
          <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <span class="text-3xl">🚚</span>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">Fast Delivery</h3>
          <p class="text-gray-600 text-sm leading-relaxed">
            Same-day and next-day delivery available for orders in Nairobi and surrounding areas
          </p>
        </div>

        <!-- Trust Factor 2: Quality Materials -->
        <div class="flex flex-col items-center text-center">
          <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <span class="text-3xl">✅</span>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">Quality Materials</h3>
          <p class="text-gray-600 text-sm leading-relaxed">
            Sourced from trusted suppliers ensuring durability and compliance with building standards
          </p>
        </div>

        <!-- Trust Factor 3: Reliable Availability -->
        <div class="flex flex-col items-center text-center">
          <div class="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
            <span class="text-3xl">📦</span>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">Reliable Availability</h3>
          <p class="text-gray-600 text-sm leading-relaxed">
            Consistent stock levels for all major materials. Real-time inventory updates
          </p>
        </div>
      </div>

      <!-- Optional: Additional features -->
      <div class="mt-12 pt-12 border-t border-gray-100">
        <p class="text-gray-600 text-center text-sm max-w-2xl mx-auto">
          Trusted by contractors and fundis across Kenya. Join hundreds of happy customers who rely on Homepoint
          for their construction material needs.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
// No props or emits for trust section
</script>

<style scoped>
.trust-section {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.02) 0%, rgba(255, 255, 255, 0) 100%);
}
</style>
