<template>
	<Dialog
    	v-model:visible="visible"
    	modal
    	header="Order History"
    	:style="{ width: '95vw', maxWidth: '1200px' }"
  />
  <div class="pending-orders-container">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Pending Orders</h1>
        <p class="text-sm text-gray-600 mt-1">Orders awaiting payment confirmation</p>
      </div>
      <Button
        icon="pi pi-refresh"
        label="Refresh"
        :loading="orderStore.loading"
        @click="refreshOrders"
      />
    </div>

    <Message v-if="orderStore.error" severity="error" :closable="true" @close="orderStore.clearError()">
      {{ orderStore.error }}
    </Message>

    <div v-if="orderStore.loading && !orderStore.pendingOrders.length" class="text-center py-12">
      <ProgressSpinner />
      <p class="text-gray-600 mt-4">Loading pending orders...</p>
    </div>

    <div v-else-if="!orderStore.pendingOrders.length" class="text-center py-12">
      <i class="pi pi-inbox text-6xl text-gray-300 mb-4"></i>
      <h3 class="text-xl font-semibold text-gray-700 mb-2">No Pending Orders</h3>
      <p class="text-gray-600 mb-6">All orders have been completed or there are no orders yet.</p>
      <Button
        label="Back to Shop"
        icon="pi pi-shopping-cart"
        @click="$router.push({ name: 'shop' })"
      />
    </div>

    <div v-else class="space-y-4">
      <Card v-for="order in orderStore.pendingOrders" :key="order.id" class="order-card">
        <template #header>
          <div class="flex items-center justify-between p-4 border-b border-gray-200">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">Order #{{ order.id }}</h3>
              <p class="text-sm text-gray-600">{{ formatDate(order.created_at) }}</p>
            </div>
            <Tag :severity="getStatusSeverity(order.status)" :value="order.status" />
          </div>
        </template>

        <template #content>
          <div class="space-y-4">
            <!-- Order Details -->
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-600">Phone:</span>
                <span class="ml-2 font-medium">{{ order.phone_number }}</span>
              </div>
              <div>
                <span class="text-gray-600">Payment Method:</span>
                <span class="ml-2 font-medium">{{ order.payment_method?.toUpperCase() || 'N/A' }}</span>
              </div>
              <div class="col-span-2">
                <span class="text-gray-600">Delivery:</span>
                <span class="ml-2 font-medium">{{ order.delivery_location }}</span>
              </div>
              <div class="col-span-2">
                <span class="text-gray-600">Total Amount:</span>
                <span class="ml-2 font-semibold text-lg text-primary-600">KES {{ formatPrice(order.total_amount) }}</span>
              </div>
            </div>

            <!-- Order Items -->
            <div v-if="order.items && order.items.length" class="border-t border-gray-200 pt-4">
              <h4 class="text-sm font-semibold text-gray-700 mb-2">Order Items</h4>
              <div class="space-y-2">
                <div
                  v-for="item in order.items"
                  :key="item.id"
                  class="flex justify-between text-sm"
                >
                  <span class="text-gray-600">{{ item.product_name }} × {{ item.quantity }}</span>
                  <span class="font-medium">KES {{ formatPrice(item.subtotal) }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <template #footer>
          <div class="flex gap-3">
            <Button
              v-if="order.payment_method === 'mpesa'"
              label="Check M-Pesa Status"
              icon="pi pi-sync"
              severity="info"
              outlined
              :loading="checkingStatus[order.id]"
              @click="checkPaymentStatus(order.id)"
            />
            <Button
              v-if="order.payment_method === 'mpesa'"
              label="Complete M-Pesa Payment"
              icon="pi pi-check"
              severity="success"
              @click="showMpesaDialog(order)"
            />
            <Button
              v-if="order.payment_method === 'cash'"
              label="Complete Cash Payment"
              icon="pi pi-money-bill"
              severity="success"
              @click="showCashDialog(order)"
            />
            <Button
              label="View Details"
              icon="pi pi-eye"
              severity="secondary"
              outlined
              @click="viewOrderDetails(order)"
            />
          </div>
        </template>
      </Card>
    </div>

    <!-- M-Pesa Payment Dialog -->
    <Dialog
      v-model:visible="mpesaDialog.visible"
      modal
      header="Complete M-Pesa Payment"
      :style="{ width: '28rem' }"
    >
      <form @submit.prevent="completeMpesaPayment" class="space-y-4">
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p class="text-sm text-blue-800">
            <strong>Order #{{ mpesaDialog.order?.id }}</strong>
          </p>
          <p class="text-sm text-blue-700 mt-1">
            Amount: <strong>KES {{ formatPrice(mpesaDialog.order?.total_amount) }}</strong>
          </p>
        </div>

        <div class="field">
          <label for="mpesa-receipt" class="block text-sm font-medium text-gray-700 mb-1">
            M-Pesa Receipt Number <span class="text-red-500">*</span>
          </label>
          <InputText
            id="mpesa-receipt"
            v-model="mpesaDialog.receiptNumber"
            placeholder="e.g. SFK1A2B3C4"
            class="w-full"
            :class="{ 'p-invalid': mpesaDialog.errors.receiptNumber }"
          />
          <small v-if="mpesaDialog.errors.receiptNumber" class="p-error">
            {{ mpesaDialog.errors.receiptNumber }}
          </small>
        </div>

        <div class="field">
          <label for="mpesa-phone" class="block text-sm font-medium text-gray-700 mb-1">
            Phone Number <span class="text-red-500">*</span>
          </label>
          <InputText
            id="mpesa-phone"
            v-model="mpesaDialog.phoneNumber"
            placeholder="254XXXXXXXXX"
            class="w-full"
            :class="{ 'p-invalid': mpesaDialog.errors.phoneNumber }"
          />
          <small v-if="mpesaDialog.errors.phoneNumber" class="p-error">
            {{ mpesaDialog.errors.phoneNumber }}
          </small>
        </div>

        <Message v-if="mpesaDialog.error" severity="error" :closable="false">
          {{ mpesaDialog.error }}
        </Message>

        <div class="flex gap-3 pt-4">
          <Button
            type="button"
            label="Cancel"
            severity="secondary"
            outlined
            class="flex-1"
            @click="mpesaDialog.visible = false"
          />
          <Button
            type="submit"
            label="Complete Payment"
            icon="pi pi-check"
            class="flex-1"
            :loading="mpesaDialog.loading"
          />
        </div>
      </form>
    </Dialog>

    <!-- Cash Payment Dialog -->
    <Dialog
      v-model:visible="cashDialog.visible"
      modal
      header="Complete Cash Payment"
      :style="{ width: '28rem' }"
    >
      <form @submit.prevent="completeCashPayment" class="space-y-4">
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <p class="text-sm text-green-800">
            <strong>Order #{{ cashDialog.order?.id }}</strong>
          </p>
          <p class="text-sm text-green-700 mt-1">
            Expected Amount: <strong>KES {{ formatPrice(cashDialog.order?.total_amount) }}</strong>
          </p>
        </div>

        <div class="field">
          <label for="cash-amount" class="block text-sm font-medium text-gray-700 mb-1">
            Amount Received <span class="text-red-500">*</span>
          </label>
          <InputNumber
            id="cash-amount"
            v-model="cashDialog.amount"
            mode="currency"
            currency="KES"
            locale="en-KE"
            class="w-full"
            :class="{ 'p-invalid': cashDialog.errors.amount }"
            :min="0"
          />
          <small v-if="cashDialog.errors.amount" class="p-error">
            {{ cashDialog.errors.amount }}
          </small>
        </div>

        <div class="field">
          <label for="cash-receipt" class="block text-sm font-medium text-gray-700 mb-1">
            Receipt Number (Optional)
          </label>
          <InputText
            id="cash-receipt"
            v-model="cashDialog.receiptNumber"
            placeholder="e.g. CR-001"
            class="w-full"
          />
        </div>

        <Message v-if="cashDialog.error" severity="error" :closable="false">
          {{ cashDialog.error }}
        </Message>

        <div class="flex gap-3 pt-4">
          <Button
            type="button"
            label="Cancel"
            severity="secondary"
            outlined
            class="flex-1"
            @click="cashDialog.visible = false"
          />
          <Button
            type="submit"
            label="Complete Payment"
            icon="pi pi-check"
            class="flex-1"
            :loading="cashDialog.loading"
          />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import { useOrderStore } from '@/stores/order'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const router = useRouter()
const toast = useToast()
const orderStore = useOrderStore()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const checkingStatus = ref({})

const mpesaDialog = ref({
  visible: false,
  order: null,
  receiptNumber: '',
  phoneNumber: '',
  loading: false,
  error: '',
  errors: {
    receiptNumber: '',
    phoneNumber: '',
  },
})

const cashDialog = ref({
  visible: false,
  order: null,
  amount: 0,
  receiptNumber: '',
  loading: false,
  error: '',
  errors: {
    amount: '',
  },
})

onMounted(() => {
  refreshOrders()
})

const refreshOrders = async () => {
  await orderStore.fetchPendingOrders()
}

const formatPrice = (price) => {
  if (!price && price !== 0) return '0.00'
  return Number.parseFloat(price).toFixed(2)
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const getStatusSeverity = (status) => {
  const severityMap = {
    PENDING: 'warning',
    COMPLETED: 'success',
    CANCELLED: 'danger',
    PROCESSING: 'info',
  }
  return severityMap[status] || 'info'
}

const checkPaymentStatus = async (orderId) => {
  checkingStatus.value[orderId] = true

  const result = await orderStore.checkMpesaPaymentStatus(orderId)

  checkingStatus.value[orderId] = false

  if (result.success) {
    toast.add({
      severity: result.order?.status === 'COMPLETED' ? 'success' : 'info',
      summary: 'Payment Status',
      detail: result.message || `Order status: ${result.status}`,
      life: 3000,
    })
  } else {
    toast.add({
      severity: 'error',
      summary: 'Status Check Failed',
      detail: result.error,
      life: 3000,
    })
  }
}

const showMpesaDialog = (order) => {
  mpesaDialog.value = {
    visible: true,
    order,
    receiptNumber: '',
    phoneNumber: order.phone_number || '',
    loading: false,
    error: '',
    errors: {
      receiptNumber: '',
      phoneNumber: '',
    },
  }
}

const validateMpesaForm = () => {
  mpesaDialog.value.errors = {
    receiptNumber: '',
    phoneNumber: '',
  }
  let valid = true

  if (!mpesaDialog.value.receiptNumber.trim()) {
    mpesaDialog.value.errors.receiptNumber = 'Receipt number is required'
    valid = false
  }

  if (!mpesaDialog.value.phoneNumber.trim()) {
    mpesaDialog.value.errors.phoneNumber = 'Phone number is required'
    valid = false
  }

  return valid
}

const completeMpesaPayment = async () => {
  if (!validateMpesaForm()) return

  mpesaDialog.value.loading = true
  mpesaDialog.value.error = ''

  const result = await orderStore.completeMpesaPayment(
    mpesaDialog.value.order.id,
    mpesaDialog.value.receiptNumber,
    mpesaDialog.value.phoneNumber
  )

  mpesaDialog.value.loading = false

  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Payment Completed',
      detail: result.message,
      life: 3000,
    })
    mpesaDialog.value.visible = false
    await refreshOrders()
  } else {
    mpesaDialog.value.error = result.error
  }
}

const showCashDialog = (order) => {
  cashDialog.value = {
    visible: true,
    order,
    amount: order.total_amount || 0,
    receiptNumber: '',
    loading: false,
    error: '',
    errors: {
      amount: '',
    },
  }
}

const validateCashForm = () => {
  cashDialog.value.errors = {
    amount: '',
  }
  let valid = true

  if (!cashDialog.value.amount || cashDialog.value.amount <= 0) {
    cashDialog.value.errors.amount = 'Amount must be greater than zero'
    valid = false
  }

  return valid
}

const completeCashPayment = async () => {
  if (!validateCashForm()) return

  cashDialog.value.loading = true
  cashDialog.value.error = ''

  const result = await orderStore.completeCashPayment(
    cashDialog.value.order.id,
    cashDialog.value.amount,
    cashDialog.value.receiptNumber
  )

  cashDialog.value.loading = false

  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Payment Completed',
      detail: result.message,
      life: 3000,
    })
    cashDialog.value.visible = false
    await refreshOrders()
  } else {
    cashDialog.value.error = result.error
  }
}

const viewOrderDetails = (order) => {
  router.push({ name: 'order-details', params: { id: order.id } })
}
</script>

<style scoped>
.pending-orders-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.order-card :deep(.p-card-body) {
  padding: 0;
}

.order-card :deep(.p-card-content) {
  padding: 1rem;
}

.order-card :deep(.p-card-footer) {
  padding: 1rem;
  background-color: #f9fafb;
  border-top: 1px solid #e5e7eb;
}
</style>
