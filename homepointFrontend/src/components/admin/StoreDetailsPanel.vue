<template>
  <div class="p-4">
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
        <div>
          <h2 class="text-xl font-bold text-gray-800">Store Details & Settings</h2>
          <p class="text-sm text-gray-600 mt-1">Configure your business information for receipts and reports</p>
        </div>
        <Button 
          label="Save Settings" 
          icon="pi pi-save" 
          :loading="isSaving" 
          @click="saveSettings" 
        />
      </div>

      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <!-- General Information -->
          <div class="space-y-4">
            <h3 class="text-lg font-semibold text-gray-700 border-b pb-2 mb-4 flex items-center gap-2">
              <i class="pi pi-home text-blue-600"></i>
              General Information
            </h3>
            
            <div class="flex flex-col gap-2">
              <label for="storeName" class="text-sm font-bold text-gray-700">Store Name</label>
              <InputText id="storeName" v-model="settings.name" placeholder="e.g. HOMEPOINT HARDWARE STORE" />
            </div>

            <div class="flex flex-col gap-2">
              <label for="storePhone" class="text-sm font-bold text-gray-700">Phone Number</label>
              <InputText id="storePhone" v-model="settings.phone" placeholder="+254 700 000000" />
            </div>

            <div class="flex flex-col gap-2">
              <label for="storeEmail" class="text-sm font-bold text-gray-700">Email Address</label>
              <InputText id="storeEmail" v-model="settings.email" placeholder="contact@homepoint.com" />
            </div>

            <div class="flex flex-col gap-2">
              <label for="storeAddress" class="text-sm font-bold text-gray-700">Physical Address</label>
              <Textarea id="storeAddress" v-model="settings.address" rows="3" autoResize placeholder="Nairobi, Kenya" />
            </div>
          </div>

          <!-- Tax & Compliance -->
          <div class="space-y-4">
            <h3 class="text-lg font-semibold text-gray-700 border-b pb-2 mb-4 flex items-center gap-2">
              <i class="pi pi-file-check text-green-600"></i>
              Tax & Compliance (eTIMS)
            </h3>

            <div class="flex flex-col gap-2">
              <label for="tin" class="text-sm font-bold text-gray-700">Tax Identification Number (TIN)</label>
              <InputText id="tin" v-model="settings.tin" placeholder="118184471" />
              <small class="text-gray-500 italic">Used for internal audit and KRA reporting</small>
            </div>

            <div class="flex flex-col gap-2">
              <label for="pin" class="text-sm font-bold text-gray-700">KRA PIN</label>
              <InputText id="pin" v-model="settings.pin" placeholder="A00XXXXXXXXX" />
            </div>

            <div class="flex flex-col gap-2">
              <label for="vatRate" class="text-sm font-bold text-gray-700">Standard VAT Rate (%)</label>
              <InputNumber id="vatRate" v-model="settings.vatRate" suffix="%" :min="0" :max="100" />
            </div>

            <div class="bg-blue-50 p-4 rounded-lg border border-blue-100 mt-4">
              <h4 class="text-sm font-bold text-blue-800 mb-2">Compliance Note:</h4>
              <p class="text-xs text-blue-700 leading-relaxed">
                Ensure these details match your official KRA registration. These values are used to generate the QR codes and signatures required for eTIMS-compliant receipts.
              </p>
            </div>
          </div>

          <!-- System Defaults -->
          <div class="md:col-span-2 space-y-4 pt-4">
            <h3 class="text-lg font-semibold text-gray-700 border-b pb-2 mb-4 flex items-center gap-2">
              <i class="pi pi-cog text-purple-600"></i>
              Receipt Customization
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="flex flex-col gap-2">
                <label for="receiptHeader" class="text-sm font-bold text-gray-700">Receipt Header Note</label>
                <Textarea id="receiptHeader" v-model="settings.receiptHeader" rows="2" placeholder="Welcome to Homepoint" />
              </div>
              <div class="flex flex-col gap-2">
                <label for="receiptFooter" class="text-sm font-bold text-gray-700">Receipt Footer Note</label>
                <Textarea id="receiptFooter" v-model="settings.receiptFooter" rows="2" placeholder="Goods once sold are not returnable" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

const toast = useToast()
const isSaving = ref(false)

// Initial default settings
const settings = reactive({
  name: '',
  phone: '',
  email: '',
  address: '',
  tin: '',
  pin: '',
  vatRate: 16,
  receiptHeader: 'Thank you for your purchase!',
  receiptFooter: 'Powered by HOMEPOINT POS'
})

onMounted(() => {
  loadSettings()
})

const loadSettings = () => {
  const saved = localStorage.getItem('store_settings')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      Object.assign(settings, parsed)
    } catch (e) {
      console.error('Failed to parse saved settings', e)
    }
  } else {
    // Fallback to env or defaults
    settings.name = import.meta.env.VITE_STORE_NAME || 'HOMEPOINT HARDWARE STORE'
    settings.tin = import.meta.env.VITE_STORE_TIN || '118184471'
    settings.phone = import.meta.env.VITE_STORE_PHONE || '+254 700 000000'
    settings.address = import.meta.env.VITE_STORE_ADDRESS || 'Nairobi, Kenya'
  }
}

const saveSettings = async () => {
  isSaving.value = true
  
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 800))
  
  try {
    localStorage.setItem('store_settings', JSON.stringify(settings))
    
    toast.add({
      severity: 'success',
      summary: 'Settings Saved',
      detail: 'Store information has been updated successfully',
      life: 3000
    })
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save settings',
      life: 3000
    })
  } finally {
    isSaving.value = false
  }
}
</script>
