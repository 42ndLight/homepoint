<template>
  <Drawer
    v-model:visible="visible"
    position="right"
    :modal="true"
    :dismissableMask="true"
    :breakpoints="{ '960px': '90vw', '640px': '100vw' }"
    :style="{ width: '420px' }"
    class="p-0"
    @show="onShow"
  >
    <div class="flex flex-col h-full">
      <div class="p-4 border-b border-gray-200">
        <h2 class="text-xl font-semibold">Orders</h2>
      </div>

      <Tabs value="Pending" class="flex-1 flex flex-col">
          <TabList>
              <Tab value="Pending">Pending</Tab>
              <Tab value="Completed">Completed</Tab>
              <Tab value="History">History</Tab>
          </TabList>
          <TabPanels>
              <TabPanel value="Pending">
                <div class="p-4 overflow-auto flex-1">
                  <div v-if="orderStore.loading" class="flex      justify-center py-12">
                    <ProgressSpinner />
                  </div>
                  <div v-else-if="pendingOrders.length === 0  "     class="text-center py-12  text-gray-500">
                    <i class="pi pi-inbox text-4xl mb-3       opacity-50"></i>
                    <p>No pending orders</p>
                  </div>
                  <div v-else class="space-y-4">
                    <div
                      v-for="order in pendingOrders"
                      :key="order.id"
                      class="border border-gray-200   rounded-lg    overflow-hidden"
                    >
                      <div class="p-4 border-b  border-gray-100    bg-gray-50">
                        <div class="flex justify-between      items-start">
                          <div>
                            <h3 class="font-semibold      text-gray-900">Order #{{ order. id }}  </h3>
                            <p class="text-sm text-gray-600"  >{{     formatDate(order. created_at) }}</p    >
                          </div>
                          <Tag :severity="getStatusSeverity(      order.status)" :value=" formatStatus(    order.status)"  />
                        </div>
                      </div>
                      <div class="p-4 space-y-3">
                        <div class="grid grid-cols-2 gap-2      text-sm">
                          <div>
                            <span class="text-gray-500">  Phone:</    span>
                            <span class="ml-1 font-medium"> {{     order.phone_number }}</ span>
                          </div>
                          <div class="col-span-2">
                            <span class="text-gray-500">      Delivery:</span>
                            <span class="ml-1 font-medium"> {{     order.delivery_location   }}</span>
                          </div>
                          <div class="col-span-2">
                            <span class="text-gray-500">  Total:</    span>
                            <span class="ml-1 font-semibold      text-primary-600">KES {{  formatPrice    (order. total_amount) }}</span>
                          </div>
                        </div>
                        <div v-if="order.items?.length"   class="   border-t border-gray-100  pt-3">
                          <h4 class="text-xs font-semibold      text-gray-500 uppercase mb-2">  Items</   h4>
                          <div class="space-y-1 text-sm">
                            <div v-for="(item, i) in order. items    " :key="i" class="  flex    justify-between">
                              <span class="text-gray-600">{{      item.sku }} × {{ item.  quantity    }}</span>
                              <span class="font-medium">KES   {{    formatPrice((item.price   || item.  price_at_purchase)   * item.   quantity) }}</ span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="p-4 border-t  border-gray-100    flex flex-wrap justify-end  gap-2">
                        <Button
                          label="Check M-Pesa"
                          icon="pi pi-sync"
                          severity="info"
                          size="small"
                          outlined
                          :loading="checkingOrderId ===   order.id    "
                          @click="checkMpesaStatus(order.id)  "
                        />
                        <Button
                          label="STK Push"
                          icon="pi pi-mobile"
                          severity="warn"
                          size="small"
                          :loading="initiatingStkId === order.id"
                          @click="initiateStk(order)"
                        />
                        <Button
                          label="Complete M-Pesa"
                          icon="pi pi-check"
                          severity="success"
                          size="small"
                          @click="openMpesaDialog(order)"
                        />
                        <Button
                          label="Complete Cash"
                          icon="pi pi-money-bill"
                          severity="secondary"
                          size="small"
                          outlined
                          @click="openCashDialog(order)"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </TabPanel>
      
              <TabPanel value="Completed">
                <div class="p-4 overflow-auto">
                  <div v-if="orderStore.loading && activeTab   ===     1" class="flex justify-center  py-12">
                    <ProgressSpinner />
                  </div>
                  <div v-else-if="completedOrders.length ===   0"     class="text-center py-12  text-gray-500">
                    <i class="pi pi-check-circle text-4xl   mb-3    opacity-50"></i>
                    <p>No completed orders</p>
                  </div>
                  <div v-else class="space-y-3">
                    <div
                      v-for="order in completedOrders"
                      :key="order.id"
                      class="border border-gray-200   rounded-lg    p-4"
                    >
                      <div class="flex justify-between      items-center">
                        <div>
                          <span class="font-medium">#{{   order.id     }}</span>
                          <span class="text-sm text-gray-500      ml-2">{{ formatDate(order.  created_at)   }}</span>
                        </div>
                        <div class="text-right">
                          <Tag :severity="getStatusSeverity(      order.status)" :value=" formatStatus(    order.status)"  />
                          <div class="font-semibold text-sm   mt-1    ">KES {{ formatPrice(order  .   total_amount) }}</div>
                        </div>
                      </div>
                      <div class="mt-3 flex gap-2">
                        <Button
                          label="Receipt"
                          icon="pi pi-receipt"
                          size="small"
                          class="flex-1"
                          @click="viewReceipt(order.id)"
                        />
                        <Button
                          label="Reprint"
                          icon="pi pi-print"
                          severity="secondary"
                          size="small"
                          outlined
                          @click="printReceipt(order.id)"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </TabPanel>
      
              <TabPanel value="History">
                <div class="p-4 overflow-auto">
                  <div v-if="orderStore.loading && activeTab   ===     2" class="flex justify-center  py-12">
                    <ProgressSpinner />
                  </div>
                  <div v-else-if="orderStore.orderHistory.  length     === 0" class="text-center  py-12    text-gray-500">
                    <i class="pi pi-history text-4xl mb-3      opacity-50"></i>
                    <p>No orders yet</p>
                  </div>
                  <div v-else class="space-y-2">
                    <div
                      v-for="order in orderStore. orderHistory"
                      :key="order.id"
                      class="flex justify-between   items-center    py-3 border-b   border-gray-100   last:border-0"
                    >
                      <div>
                        <span class="font-medium">#{{ order.  id    }}</span>
                        <span class="text-sm text-gray-500  ml-2"    >{{ formatDate(order. created_at) }}</   span>
                      </div>
                      <div class="text-right">
                        <Tag :severity="getStatusSeverity(  order.    status)" :value=" formatStatus(order.    status)" />
                        <div class="font-semibold text-sm   mt-1">    KES {{ formatPrice(order. total_amount)    }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </TabPanel>
        </TabPanels>
      </Tabs>

      <div class="p-4 border-t border-gray-200">
        <Button label="Refresh" icon="pi pi-refresh" outlined class="w-full" @click="refreshOrders" />
      </div>
    </div>

    <!-- M-Pesa completion dialog -->
    <Dialog
      v-model:visible="mpesaDialogVisible"
      header="Complete M-Pesa Payment"
      :modal="true"
      :style="{ width: '360px' }"
      :closable="!orderStore.loading"
    >
      <div class="space-y-4">
        <p v-if="mpesaOrder" class="text-gray-600 text-sm">
          Order #{{ mpesaOrder.id }} — KES {{ formatPrice(mpesaOrder.total_amount) }}
        </p>
        <div class="field">
          <label for="mpesa-receipt" class="block text-sm font-medium mb-1">M-Pesa receipt number</label>
          <InputText id="mpesa-receipt" v-model="mpesaForm.receiptNumber" placeholder="e.g. QGH12345XY" class="w-full" />
        </div>
        <div class="field">
          <label for="mpesa-phone" class="block text-sm font-medium mb-1">Phone number</label>
          <InputText id="mpesa-phone" v-model="mpesaForm.phone" placeholder="254712345678" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" outlined @click="mpesaDialogVisible = false" :disabled="orderStore.loading" />
        <Button label="Confirm" icon="pi pi-check" :loading="orderStore.loading" @click="submitMpesaComplete" />
      </template>
    </Dialog>

    <!-- Cash completion dialog -->
    <Dialog
      v-model:visible="cashDialogVisible"
      header="Complete Cash Payment"
      :modal="true"
      :style="{ width: '360px' }"
      :closable="!orderStore.loading"
    >
      <div class="space-y-4">
        <p v-if="cashOrder" class="text-gray-600 text-sm">
          Order #{{ cashOrder.id }} — KES {{ formatPrice(cashOrder.total_amount) }}
        </p>
        <div class="field">
          <label for="cash-amount" class="block text-sm font-medium mb-1">Amount received (optional)</label>
          <InputNumber id="cash-amount" v-model="cashForm.amount" mode="decimal" :minFractionDigits="2" placeholder="0.00" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" outlined @click="cashDialogVisible = false" :disabled="orderStore.loading" />
        <Button label="Confirm" icon="pi pi-check" :loading="orderStore.loading" @click="submitCashComplete" />
      </template>
    </Dialog>
  </Drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import Drawer from 'primevue/drawer'
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import ProgressSpinner from 'primevue/progressspinner'
import { useOrderStore } from '@/stores/order'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const orderStore = useOrderStore()
const toast = useToast()

const activeTab = ref(0)
const checkingOrderId = ref(null)
const initiatingStkId = ref(null)
const mpesaDialogVisible = ref(false)
const cashDialogVisible = ref(false)
const mpesaOrder = ref(null)
const cashOrder = ref(null)

const mpesaForm = ref({ receiptNumber: '', phone: '' })
const cashForm = ref({ amount: null })

const pendingOrders = computed(() => orderStore.pendingOrders)
const completedOrders = computed(() =>
  orderStore.orderHistory.filter((o) => {
    const s = (o.status || '').toLowerCase()
    return s === 'paid' || s === 'delivered'
  })
)

const formatPrice = (p) => {
  if (p == null || (p !== 0 && !p)) return '0.00'
  return Number.parseFloat(p).toFixed(2)
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleString('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatStatus = (status) => {
  const s = (status || '').toLowerCase()
  const map = { pending: 'Pending', paid: 'Paid', delivered: 'Delivered', cancelled: 'Cancelled' }
  return map[s] || status || 'Unknown'
}

const getStatusSeverity = (status) => {
  const s = (status || '').toLowerCase()
  const map = { pending: 'warn', paid: 'success', delivered: 'success', cancelled: 'danger' }
  return map[s] || 'info'
}

const onShow = () => refreshOrders()

const refreshOrders = async () => {
  const res = await orderStore.fetchOrderHistory()
  if (!res.success && res.error) {
    toast.add({ severity: 'error', summary: 'Error', detail: res.error, life: 3000 })
  }
}

const checkMpesaStatus = async (orderId) => {
  checkingOrderId.value = orderId
  try {
    const res = await orderStore.checkMpesaPaymentStatus(orderId)
    if (res.success) {
      toast.add({ severity: 'info', summary: 'M-Pesa Status', detail: res.message || res.status, life: 3000 })
    } else {
      toast.add({ severity: 'error', summary: 'Error', detail: res.error, life: 3000 })
    }
  } finally {
    checkingOrderId.value = null
  }
}

const initiateStk = async (order) => {
  if (initiatingStkId.value === order.id) return // Prevent multiple clicks for same order
  
  initiatingStkId.value = order.id
  try {
    const res = await orderStore.initiateStkPush(order.id, order.phone_number)
    if (res.success) {
      if (res.is_duplicate) {
        toast.add({ 
          severity: 'info', 
          summary: 'Pending Payment', 
          detail: res.message, 
          life: 5000 
        })
      } else {
        toast.add({ 
          severity: 'success', 
          summary: 'STK Push Sent', 
          detail: 'Prompt sent to customer phone. Ask them to enter their PIN.', 
          life: 5000 
        })
      }
    } else {
      toast.add({ severity: 'error', summary: 'STK Push Failed', detail: res.error, life: 3000 })
    }
  } finally {
    initiatingStkId.value = null
  }
}

const openMpesaDialog = (order) => {
  mpesaOrder.value = order
  mpesaForm.value = { receiptNumber: '', phone: order.phone_number || '' }
  mpesaDialogVisible.value = true
}

const openCashDialog = (order) => {
  cashOrder.value = order
  cashForm.value = { amount: order.total_amount ? Number(order.total_amount) : null }
  cashDialogVisible.value = true
}

const submitMpesaComplete = async () => {
  if (!mpesaOrder.value) return
  const { receiptNumber, phone } = mpesaForm.value
  const receipt = receiptNumber?.trim()
  const phoneVal = phone?.trim()
  if (receipt && phoneVal) {
    const res = await orderStore.completeMpesaPayment(mpesaOrder.value.id, receipt, phoneVal)
    if (res.success) {
      toast.add({ severity: 'success', summary: 'Payment Complete', detail: res.message, life: 3000 })
      mpesaDialogVisible.value = false
      mpesaOrder.value = null
    } else {
      toast.add({ severity: 'error', summary: 'Error', detail: res.error, life: 3000 })
    }
  } else {
    toast.add({ severity: 'warn', summary: 'Required', detail: 'Receipt number and phone are required', life: 3000 })
  }
}

const submitCashComplete = async () => {
  const order = cashOrder.value
  const transaction_type = 'SALES'
  if (order) {
    const amount = cashForm.value.amount != null ? String(cashForm.value.amount) : ''
    const res = await orderStore.completeCashPayment(order.id, amount, transaction_type)
    if (res.success) {
      toast.add({ severity: 'success', summary: 'Payment Recorded', detail: res.message, life: 3000 })
      cashDialogVisible.value = false
      cashOrder.value = null
    } else {
      toast.add({ severity: 'error', summary: 'Error', detail: res.error, life: 3000 })
    }
  }
}

const viewReceipt = (orderId) => {
  router.push({ name: 'receipt', params: { orderId } })
}

const printReceipt = (orderId) => {
  router.push({ name: 'receipt', params: { orderId } })
  // In ReceiptView, the print dialog can be triggered automatically or by user
}

watch(activeTab, () => {
  if (activeTab.value === 1 || activeTab.value === 2) {
    refreshOrders()
  }
})
</script>
