<template>
  <footer class="bg-gray-900 text-gray-100 py-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
        <!-- Company Info -->
        <div>
          <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
            <div class="w-6 h-6 bg-blue-600 rounded"></div>
            Homepoint
          </h3>
          <p class="text-sm text-gray-400">
            Your trusted supplier of quality construction materials in Kenya.
          </p>
        </div>

        <!-- Quick Links -->
        <div>
          <h4 class="text-sm font-semibold mb-4 text-white">Quick Links</h4>
          <ul class="space-y-2 text-sm">
            <li><a href="#" class="text-gray-400 hover:text-white transition">Browse Materials</a></li>
            <li><a href="#" class="text-gray-400 hover:text-white transition">Request Quote</a></li>
            <li><a href="#" class="text-gray-400 hover:text-white transition">Track Order</a></li>
            <li><a href="#" class="text-gray-400 hover:text-white transition">Contact Us</a></li>
          </ul>
        </div>

        <!-- Categories -->
        <div>
          <h4 class="text-sm font-semibold mb-4 text-white">Categories</h4>
          <ul class="space-y-2 text-sm">
            <li><a href="#" class="text-gray-400 hover:text-white transition">Cement & Concrete</a></li>
            <li><a href="#" class="text-gray-400 hover:text-white transition">Steel & Iron</a></li>
            <li><a href="#" class="text-gray-400 hover:text-white transition">Plumbing</a></li>
            <li><a href="#" class="text-gray-400 hover:text-white transition">Electrical</a></li>
          </ul>
        </div>

        <!-- Contact Info -->
        <div>
          <h4 class="text-sm font-semibold mb-4 text-white">Contact</h4>
          <ul class="space-y-3 text-sm">
            <li class="flex items-center gap-2">
              <span>📞</span>
              <a href="tel:+254712345678" class="text-gray-400 hover:text-white transition">+254 712 345 678</a>
            </li>
            <li class="flex items-center gap-2">
              <span>📧</span>
              <a href="mailto:info@homepoint.ke" class="text-gray-400 hover:text-white transition">info@homepoint.ke</a>
            </li>
            <li class="flex items-center gap-2">
              <span>📍</span>
              <span class="text-gray-400">Nairobi, Kenya</span>
            </li>
            <li class="flex items-center gap-2">
              <span>⏰</span>
              <span class="text-gray-400">6am - 6pm Daily</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Divider -->
      <div class="border-t border-gray-800 my-8"></div>

      <!-- Bottom Section -->
      <div class="flex flex-col md:flex-row justify-between items-center text-sm text-gray-400">
        <p>&copy; 2026 Homepoint. All rights reserved.</p>
        <div class="flex gap-4 mt-4 md:mt-0">
          <a href="#" class="hover:text-white transition">Privacy Policy</a>
          <a href="#" class="hover:text-white transition">Terms of Service</a>
          <a href="#" class="hover:text-white transition">Contact</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
// No data needed
</script>

<style scoped>
footer {
  margin-top: auto;
}
</style>
