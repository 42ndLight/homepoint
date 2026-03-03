import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import { useCartStore } from './cart'

export const useOrderStore = defineStore('order', () => {
  const currentOrder = ref(null)
  const orderHistory = ref([])
  const loading = ref(false)
  const error = ref(null)

  const hasCurrentOrder = computed(() => !!currentOrder.value)
  const currentOrderId = computed(() => currentOrder.value?.id)
  const currentOrderStatus = computed(() => currentOrder.value?.status)

  const createOrder = async (cartItems, customerPhone, deliveryLocation, paymentMethod = 'mpesa') => {
    const cartStore = useCartStore()
    loading.value = true
    error.value = null

    try {
      const items = cartItems.map(item => ({
        variant_id: item.variant_id,
        quantity: item.quantity,
      }))

      const orderData = {
        phone_number: customerPhone,
        delivery_location: deliveryLocation,
        items,
      }

      const response = await api.post('/orders/orders/', orderData)

      currentOrder.value = response.order
      orderHistory.value.unshift(response.order)

      cartStore.clearCart()

      return {
        success: true,
        order: response.order,
        message: response.message,
        paymentMethod,
      }
    } catch (err) {
      error.value = err.data?.detail || err.message || 'Failed to create order'

      if (err.data?.errors) {
        error.value = err.data.errors.join(', ')
      }

      return {
        success: false,
        error: error.value,
      }
    } finally {
      loading.value = false
    }
  }

  const fetchOrder = async (orderId) => {
    loading.value = true
    error.value = null

    try {
      const order = await api.get(`/orders/orders/${orderId}/`)
      currentOrder.value = order
      return { success: true, order }
    } catch (err) {
      error.value = err.message || 'Failed to fetch order'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const fetchOrderHistory = async () => {
    loading.value = true
    error.value = null

    try {
      const orders = await api.get('/orders/orders/')
      orderHistory.value = orders.results || orders
      return { success: true, orders: orderHistory.value }
    } catch (err) {
      error.value = err.message || 'Failed to fetch order history'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const clearCurrentOrder = () => {
    currentOrder.value = null
    error.value = null
  }

  const clearError = () => {
    error.value = null
  }

  return {
    currentOrder,
    orderHistory,
    loading,
    error,
    hasCurrentOrder,
    currentOrderId,
    currentOrderStatus,
    createOrder,
    fetchOrder,
    fetchOrderHistory,
    clearCurrentOrder,
    clearError,
  }
})
