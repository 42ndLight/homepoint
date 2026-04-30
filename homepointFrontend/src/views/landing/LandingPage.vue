<template>
  <div class="internal-resources min-h-screen bg-gray-50 pb-12">
    <!-- Header Section -->
    <HeaderSection
      :name="authStore.user?.first_name || authStore.user?.username"
      :role="authStore.user?.role"
      :lastLogin="lastLoginFormatted"
    />

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 1. Performance / System Health Dashboard -->
      <StatusInfo 
        :isAdmin="authStore.isAdmin"
        :adminStats="adminStats"
        :staffStats="staffStats"
      />

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- 2. Information Section -->
        <div class="lg:col-span-2 space-y-8">
          <!-- Role Definitions Table -->
          <TrustSection :roles="roleDefinitions" />

          <!-- 3. Admin & Staff Guide -->
          <OpProcedures :guides="operationalGuides" />
        </div>

        <div class="space-y-8">
          <!-- Version History -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="p-6 border-b border-gray-100 flex items-center justify-between">
              <h2 class="text-lg font-bold text-gray-900 flex items-center gap-2">
                <i class="pi pi-history text-blue-600"></i>
                Version History
              </h2>
              <span class="text-xs font-bold px-2 py-1 bg-gray-100 rounded text-gray-600">v1.2.4</span>
            </div>
            <div class="p-6 space-y-4">
              <div v-for="update in versionHistory" :key="update.version" class="relative pl-6 pb-4 border-l-2 border-blue-100 last:border-0">
                <div class="absolute -left-[9px] top-0 w-4 h-4 bg-blue-500 rounded-full border-2 border-white"></div>
                <div class="flex justify-between items-start mb-1">
                  <span class="font-bold text-sm text-gray-900">{{ update.version }}</span>
                  <span class="text-[10px] text-gray-400 font-mono">{{ update.date }}</span>
                </div>
                <p class="text-xs text-gray-600">{{ update.change }}</p>
              </div>
            </div>
          </div>

          <!-- 4. Expanded Internal FAQ -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="p-6 border-b border-gray-100">
              <h2 class="text-lg font-bold text-gray-900 mb-4">Internal FAQ</h2>
              <div class="relative">
                <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                <input 
                  v-model="faqSearch" 
                  type="text" 
                  placeholder="Search troubleshooting..." 
                  class="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>
            <div class="p-2 space-y-1 max-h-[400px] overflow-y-auto">
              <div v-for="item in filteredFAQ" :key="item.q" class="p-4 rounded-lg hover:bg-gray-50 cursor-pointer group transition">
                <details class="group">
                  <summary class="list-none flex justify-between items-center font-bold text-sm text-gray-800">
                    {{ item.q }}
                    <i class="pi pi-chevron-down text-xs text-gray-400 group-open:rotate-180 transition"></i>
                  </summary>
                  <p class="mt-2 text-xs text-gray-600 leading-relaxed">
                    {{ item.a }}
                  </p>
                </details>
              </div>
              <div v-if="filteredFAQ.length === 0" class="p-8 text-center text-gray-400 text-sm">
                No matching FAQ items found.
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
    
    <!-- Footer -->
    <Footer />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSync } from '@/composables/useSync'
import HeaderSection from '@/components/landing/HeaderSection.vue'
import StatusInfo from '@/components/landing/StatusInfo.vue'
import TrustSection from '@/components/landing/TrustSection.vue'
import OpProcedures from '@/components/landing/OpProcedures.vue'
import Footer from '@/components/landing/Footer.vue'

const authStore = useAuthStore()
const { isOnline, lastSyncTime } = useSync()

const faqSearch = ref('')
const systemHealth = ref({
  api: 'Checking...',
  database: 'Checking...',
  mpesa: 'Active',
  etims: 'Active'
})

const lastLoginFormatted = computed(() => {
  if (!authStore.user?.last_login) return 'First time'
  return new Date(authStore.user.last_login).toLocaleString('en-KE')
})

const adminStats = computed(() => [
  { label: 'API Connectivity', value: systemHealth.value.api, icon: 'pi pi-server', iconColor: 'text-green-500' },
  { label: 'Database Health', value: systemHealth.value.database, icon: 'pi pi-database', iconColor: 'text-blue-500' },
  { label: 'M-Pesa Gateway', value: systemHealth.value.mpesa, icon: 'pi pi-mobile', iconColor: 'text-purple-500' },
  { label: 'eTIMS Service', value: systemHealth.value.etims, icon: 'pi pi-file-check', iconColor: 'text-amber-500' }
])

const staffStats = computed(() => [
  { title: 'Current Shift Status', label: 'Records Processed Today', value: '42', icon: 'pi pi-list', iconBg: 'text-blue-100 bg-blue-50' },
  { title: 'Sync Status', label: `Last Sync: ${lastSyncTime.value || 'Never'}`, value: isOnline.value ? 'Online' : 'Offline', icon: isOnline.value ? 'pi-wifi' : 'pi-wifi-off', iconBg: isOnline.value ? 'text-green-100 bg-green-50' : 'text-red-100 bg-red-50', valueClass: isOnline.value ? 'text-green-600' : 'text-red-600' },
  { title: 'Performance', label: 'System Responsiveness', value: 'High', icon: 'pi pi-chart-line', iconBg: 'text-purple-100 bg-purple-50' }
])

const roleDefinitions = [
  { 
    name: 'Staff', 
    description: 'Front-line operational staff.', 
    permissions: ['Create Sales', 'Edit Own', 'Search Catalog'] 
  },
  { 
    name: 'Manager', 
    description: 'Store and shift managers.', 
    permissions: ['All Staff +', 'View All Sales', 'Export Reports', 'Approve Fundis'] 
  },
  { 
    name: 'Super Admin', 
    description: 'System administrators.', 
    permissions: ['Full Access', 'User Management', 'System Config', 'Database Overrides'] 
  }
]

const operationalGuides = [
  {
    title: 'Onboarding Workflow',
    icon: 'pi pi-user-plus',
    steps: [
      'Enter valid Kenyan phone number.',
      'Assign correct role (Staff/Fundi/Customer).',
      'Verify identity documents for Fundis.',
      'Ensure "Verified" status is checked.'
    ]
  },
  {
    title: 'Manual Overrides',
    icon: 'pi pi-exclamation-triangle',
    steps: [
      'Locate transaction ID in Logs.',
      'Document reason for override.',
      'Admin approval required for deletions.',
      'Verify balance correction.'
    ]
  },
  {
    title: 'Data Exports',
    icon: 'pi pi-file-export',
    steps: [
      'Navigate to Reports section.',
      'Select date range and filter criteria.',
      'Choose format (PDF/Excel).',
      'Check "Secure Export" for sensitivity.'
    ]
  },
  {
    title: 'Shift Reconciliation',
    icon: 'pi pi-check-square',
    steps: [
      'Match physical cash to system total.',
      'Verify all M-Pesa receipts synced.',
      'Check for flagged sync errors.',
      'Sign off on digital shift summary.'
    ]
  }
]

const versionHistory = [
  { version: 'v1.2.4', date: 'Apr 2026', change: 'Added automated reconciliation checklists.' },
  { version: 'v1.2.0', date: 'Mar 2026', change: 'Enhanced M-Pesa STK push retry logic.' },
  { version: 'v1.1.5', date: 'Feb 2026', change: 'Migrated to centralized transaction ledger.' }
]

const faqItems = [
  {
    q: "Why can't I delete a record?",
    a: "The system uses soft deletes for auditing. Records are archived rather than permanently removed to maintain financial integrity."
  },
  {
    q: "What if a receipt fails to sync?",
    a: "Check your internet connection. If online, use the 'Retry' button in the Sync Queue located in the navigation header."
  },
  {
    q: "How do I reset a password?",
    a: "Admins can reset passwords via the User Management panel. Users can also use the 'Forgot Password' link on the login page."
  },
  {
    q: "Why is there a dashboard discrepancy?",
    a: "Dashboard analytics use a 15-minute cache. For real-time data, refer to the Transaction Logs panel directly."
  },
  {
    q: "Handling 'Duplicate Entry' errors",
    a: "This usually occurs if a SKU or Phone Number already exists. Search the database first before attempting to create a new record."
  },
  {
    q: "M-Pesa STK push doesn't trigger",
    a: "Ensure the phone number is in the correct format (e.g., 0712...) and that the device is online. Check M-Pesa gateway status on Admin Dashboard."
  },
  {
    q: "How to re-print a Z-Report?",
    a: "Navigate to the Reports module, go to the History tab, and select the specific date to generate a PDF for re-printing."
  }
]

const filteredFAQ = computed(() => {
  if (!faqSearch.value) return faqItems
  const search = faqSearch.value.toLowerCase()
  return faqItems.filter(item => 
    item.q.toLowerCase().includes(search) || 
    item.a.toLowerCase().includes(search)
  )
})

onMounted(async () => {
  if (authStore.isAdmin) {
    try {
      // Mocked health check ping
      setTimeout(() => {
        systemHealth.value.api = 'Healthy'
        systemHealth.value.database = 'Optimized'
      }, 1000)
    } catch (e) {
      systemHealth.value.api = 'Unreachable'
    }
  }
})
</script>

<style scoped>
.internal-resources {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

details summary::-webkit-details-marker {
  display: none;
}
</style>
