<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Checkout"
    :style="{ width: '28rem' }"
    :closable="!orderStore.loading"
    @hide="onHide"
  >
    <template v-if="!orderComplete">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="border-b border-gray-200 pb-4 mb-4">
          <h4 class="font-medium text-gray-700 mb-2">Order Summary</h4>
          <div class="text-sm text-gray-600 space-y-1">
            <div class="flex justify-between">
              <span>Items ({{ cartStore.itemCount }})</span>
              <span>KES {{ formatPrice(cartStore.subtotal) }}</span>
            </div>
            <div class="flex justify-between">
              <span>VAT (16%)</span>
              <span>KES {{ formatPrice(cartStore.vat) }}</span>
            </div>
            <div class="flex justify-between font-semibold text-gray-900 pt-2 border-t border-gray-100">
              <span>Total</span>
              <span>KES {{ formatPrice(cartStore.total) }}</span>
            </div>
          </div>
        </div>

        <div class="field">
          <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">
            Phone Number <span class="text-red-500">*</span>
          </label>
          <InputText
            id="phone"
            v-model="form.phone"
            placeholder="07XXXXXXXX"
            class="w-full"
            :class="{ 'p-invalid': errors.phone }"
            :disabled="orderStore.loading"
          />
          <small v-if="errors.phone" class="p-error">{{ errors.phone }}</small>
          <small class="text-gray-500 block mt-1">Used for M-Pesa payment and order updates</small>
        </div>

        <div class="field">
          <label for="location" class="block text-sm font-medium text-gray-700 mb-1">
            Delivery Location <span class="text-red-500">*</span>
          </label>
          <InputText
            id="location"
            v-model="form.deliveryLocation"
            placeholder="e.g. Westlands, Nairobi"
            class="w-full"
            :class="{ 'p-invalid': errors.deliveryLocation }"
            :disabled="orderStore.loading"
          />
          <small v-if="errors.deliveryLocation" class="p-error">{{ errors.deliveryLocation }}</small>
        </div>

        <div class="field">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Payment Method <span class="text-red-500">*</span>
          </label>
          <div class="flex gap-3">
            <div
              v-for="method in paymentMethods"
              :key="method.value"
              class="flex-1 border rounded-lg p-3 cursor-pointer transition-all"
              :class="[
                form.paymentMethod === method.value
                  ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                  : 'border-gray-200 hover:border-gray-300'
              ]"
              @click="form.paymentMethod = method.value"
            >
              <div class="flex items-center gap-2">
                <RadioButton
                  :inputId="method.value"
                  :value="method.value"
                  v-model="form.paymentMethod"
                  :disabled="orderStore.loading"
                />
                <label :for="method.value" class="cursor-pointer">
                  <div class="font-medium text-gray-900">{{ method.label }}</div>
                  <div class="text-xs text-gray-500">{{ method.description }}</div>
                </label>
              </div>
            </div>
          </div>
        </div>

        <Message v-if="orderStore.error" severity="error" :closable="false" class="mt-4">
          {{ orderStore.error }}
        </Message>

        <div class="flex gap-3 pt-4">
          <Button
            type="button"
            label="Cancel"
            severity="secondary"
            outlined
            class="flex-1"
            :disabled="orderStore.loading"
            @click="visible = false"
          />
          <Button
            type="submit"
            :label="submitLabel"
            icon="pi pi-check"
            class="flex-1"
            :loading="orderStore.loading"
            :disabled="!isFormValid || orderStore.loading"
          />
        </div>
      </form>
    </template>

    <template v-else>
      <div class="text-center py-6">
        <i class="pi pi-check-circle text-5xl text-green-500 mb-4"></i>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Order Placed Successfully!</h3>
        <p class="text-gray-600 mb-4">Order #{{ orderStore.currentOrderId }}</p>

        <div v-if="form.paymentMethod === 'mpesa'" class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <p class="text-green-800 font-medium">M-Pesa Payment</p>
          <p class="text-sm text-green-700 mt-1">
            You will receive an STK push on {{ form.phone }} to complete payment.
          </p>
        </div>

        <div v-else class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p class="text-blue-800 font-medium">Cash on Delivery</p>
          <p class="text-sm text-blue-700 mt-1">
            Please prepare KES {{ formatPrice(orderTotal) }} for payment upon delivery.
          </p>
        </div>

        <div class="text-sm text-gray-600 space-y-1 text-left bg-gray-50 rounded-lg p-4">
          <div class="flex justify-between">
            <span>Phone:</span>
            <span class="font-medium">{{ form.phone }}</span>
          </div>
          <div class="flex justify-between">
            <span>Delivery to:</span>
            <span class="font-medium">{{ form.deliveryLocation }}</span>
          </div>
          <div class="flex justify-between">
            <span>Total:</span>
            <span class="font-medium">KES {{ formatPrice(orderTotal) }}</span>
          </div>
        </div>

        <div class="flex mt-6">
          <Button
            label="Done"
            class="flex-1"
            @click="handleDone"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import RadioButton from 'primevue/radiobutton'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useCartStore } from '@/stores/cart'
import { useOrderStore } from '@/stores/order'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'order-complete'])
const cartStore = useCartStore()
const orderStore = useOrderStore()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const form = ref({
  phone: '',
  deliveryLocation: '',
  paymentMethod: 'mpesa',
})

const errors = ref({
  phone: '',
  deliveryLocation: '',
})

const orderComplete = ref(false)
const orderTotal = ref(0)

const paymentMethods = [
  {
    value: 'mpesa',
    label: 'M-Pesa',
    description: 'Pay via STK Push',
  },
  {
    value: 'cash',
    label: 'Cash',
    description: 'Pay on delivery',
  },
]

const validatePhone = (phone) => {
  const cleaned = phone.replace(/\s/g, '')
  const kenyanPattern = /^(?:254|\+254|0)?([17]\d{8})$/
  return kenyanPattern.test(cleaned)
}

const formatPhoneForAPI = (phone) => {
  const cleaned = phone.replace(/\s/g, '').replace(/^\+/, '')
  if (cleaned.startsWith('0')) {
    return '254' + cleaned.slice(1)
  }
  if (cleaned.startsWith('254')) {
    return cleaned
  }
  return '254' + cleaned
}

const isFormValid = computed(() => {
  return (
    form.value.phone.trim() &&
    validatePhone(form.value.phone) &&
    form.value.deliveryLocation.trim() &&
    form.value.paymentMethod &&
    cartStore.items.length > 0
  )
})

const submitLabel = computed(() => {
  if (form.value.paymentMethod === 'mpesa') {
    return 'Pay with M-Pesa'
  }
  return 'Place Order'
})

const formatPrice = (price) => {
  if (!price && price !== 0) return '0.00'
  return Number.parseFloat(price).toFixed(2)
}

const validateForm = () => {
  errors.value = { phone: '', deliveryLocation: '' }
  let valid = true

  if (!form.value.phone.trim()) {
    errors.value.phone = 'Phone number is required'
    valid = false
  } else if (!validatePhone(form.value.phone)) {
    errors.value.phone = 'Enter a valid Kenyan phone number'
    valid = false
  }

  if (!form.value.deliveryLocation.trim()) {
    errors.value.deliveryLocation = 'Delivery location is required'
    valid = false
  }

  return valid
}

const handleSubmit = async () => {
  if (!validateForm()) return

  orderStore.clearError()

  const formattedPhone = formatPhoneForAPI(form.value.phone)

  const totalBeforeOrder = cartStore.total

  const result = await orderStore.createOrder(
    cartStore.items,
    formattedPhone,
    form.value.deliveryLocation,
    form.value.paymentMethod
  )

  if (result.success) {
    orderTotal.value = totalBeforeOrder
    orderComplete.value = true
    emit('order-complete', result.order)
  }
}

const handleDone = () => {
  visible.value = false
}



const onHide = () => {
  if (orderComplete.value) {
    resetForm()
  }
}

const resetForm = () => {
  orderComplete.value = false
  form.value = {
    phone: '',
    deliveryLocation: '',
    paymentMethod: 'mpesa',
  }
  errors.value = { phone: '', deliveryLocation: '' }
  orderStore.clearCurrentOrder()
}

watch(visible, (newVal) => {
  if (newVal) {
    orderStore.clearError()
    orderComplete.value = false
  }
})
</script>
