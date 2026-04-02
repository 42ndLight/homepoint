<template>
  <div class="hero-section relative bg-gradient-to-r from-blue-600 to-blue-700 overflow-hidden">
    <!-- Background Image Overlay -->
    <div class="absolute inset-0 opacity-20">
      <div class="absolute inset-0 bg-black/30"></div>
      <!-- Placeholder for background image -->
      <div class="absolute inset-0 bg-gradient-to-br from-blue-900 to-blue-700"></div>
    </div>

    <!-- Content -->
    <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <!-- Left: Text Content -->
        <div class="text-white">
          <div class="inline-block mb-4 px-3 py-1 bg-blue-500/30 rounded-full">
            <span class="text-sm font-semibold">🏗️ Trusted by 500+ Contractors</span>
          </div>
          
          <h1 class="text-4xl md:text-5xl font-bold leading-tight mb-4">
            Quality Materials.<br />Real Prices.<br />Trusted Service.
          </h1>
          
          <p class="text-lg text-blue-100 mb-8 leading-relaxed">
            Same-day delivery in Nairobi. Bulk discounts. No hidden charges.
            <br />
            Cement, steel, plumbing, electrical, tools & more — all in stock.
          </p>

          <!-- CTA Buttons -->
          <div class="flex flex-col sm:flex-row gap-4 mb-8">
            <button
              @click="$emit('openModal')"
              class="px-6 py-3 bg-white text-blue-600 font-bold rounded-lg hover:bg-gray-100 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl hover:scale-105"
            >
              <span>📋</span>
              Get Quote Now
            </button>
            <button
              @click="scrollToProducts"
              class="px-6 py-3 bg-blue-500 text-white font-bold rounded-lg hover:bg-blue-400 transition-all duration-200 border-2 border-blue-400 hover:border-blue-300"
            >
              Browse Materials
            </button>
          </div>

          <!-- WhatsApp Badge -->
          <div class="flex items-center gap-3 bg-white/10 backdrop-blur-sm px-4 py-3 rounded-lg w-fit">
            <span class="text-xl">💬</span>
            <div>
              <p class="text-sm text-blue-100">Quick questions?</p>
              <a
                href="https://wa.me/254712345678?text=Hi%20Homepoint%2C%20I%20need%20a%20quote"
                target="_blank"
                rel="noopener noreferrer"
                class="font-semibold text-white hover:text-blue-50 text-sm"
              >
                WhatsApp us now
              </a>
            </div>
          </div>
        </div>

        <!-- Right: Visual Element -->
        <div class="hidden md:block">
          <div class="bg-white/10 backdrop-blur-md rounded-2xl p-8 h-72 flex items-center justify-center">
            <div class="text-center">
              <div class="text-6xl mb-4">🏗️</div>
              <p class="text-white/80 text-sm">Professional construction materials for every project</p>
              <p class="text-white/60 text-xs mt-3">✓ Same-day delivery ✓ Best prices ✓ Quality guaranteed</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Wave Divider -->
    <div class="absolute bottom-0 left-0 right-0 h-12 bg-white" style="clip-path: polygon(0 50%, 100% 0, 100% 100%, 0 100%)"></div>
  </div>
</template>

<script setup>
const scrollToProducts = () => {
  const productsSection = document.querySelector('[id="products"]')
  if (productsSection) {
    productsSection.scrollIntoView({ behavior: 'smooth' })
  } else {
    // Scroll to the products grid section
    window.scrollBy({ top: 800, behavior: 'smooth' })
  }
}

defineEmits(['openModal'])
</script>

<style scoped>
.hero-section {
  min-height: 500px;
  position: relative;
}
</style>
