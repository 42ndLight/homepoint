import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import { useCartStore } from './cart'

export const useOrderStore = defineStore('order', () => {
  const currentOrder = ref(null)
  const orderHistory = ref([])
  const pendingOrders = ref([])
  const loading = ref(false)
  const error = ref(null)

  const hasCurrentOrder = computed(() => !!currentOrder.value)
  const currentOrderId = computed(() => currentOrder.value?.id)
  const currentOrderStatus = computed(() => currentOrder.value?.status)
  const hasPendingOrders = computed(() => pendingOrders.value.length > 0)

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

      // If order is pending payment, add to pending orders
      if (response.order.status === 'pending') {
        pendingOrders.value.unshift(response.order)
      }

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

  const fetchPendingOrders = async () => {
    const result = await fetchOrderHistory()
    return { ...result, orders: pendingOrders.value }
  }

  const completeMpesaPayment = async (orderId, mpesaReceiptNumber, phoneNumber) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(`/orders/orders/${orderId}/complete-mpesa/`, {
        mpesa_receipt_number: mpesaReceiptNumber,
        phone_number: phoneNumber,
      })

      // Update order in current and pending lists
      updateOrderInLists(response.order)

      return {
        success: true,
        order: response.order,
        message: response.message || 'M-Pesa payment completed successfully',
      }
    } catch (err) {
      error.value = err.data?.detail || err.message || 'Failed to complete M-Pesa payment'
      return {
        success: false,
        error: error.value,
      }
    } finally {
      loading.value = false
    }
  }

  const completeCashPayment = async (orderId, amount = '') => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(`/payments/cash/`, {
        orderId,
        amount,
      })

      // Update order in current and pending lists
      updateOrderInLists(response.order)

      return {
        success: true,
        order: response.order,
        message: response.message || 'Cash payment completed successfully',
      }
    } catch (err) {
      error.value = err.data?.detail || err.message || 'Failed to complete cash payment'
      return {
        success: false,
        error: error.value,
      }
    } finally {
      loading.value = false
    }
  }

  const checkMpesaPaymentStatus = async (orderId) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/orders/orders/${orderId}/mpesa-status/`)
      
      // Update order in lists if status changed
      if (response.order) {
        updateOrderInLists(response.order)
      }

      return {
        success: true,
        status: response.status,
        order: response.order,
        message: response.message,
      }
    } catch (err) {
      error.value = err.message || 'Failed to check M-Pesa status'
      return {
        success: false,
        error: error.value,
      }
    } finally {
      loading.value = false
    }
  }

  const updateOrderInLists = (updatedOrder) => {
    // Update current order
    if (currentOrder.value?.id === updatedOrder.id) {
      currentOrder.value = updatedOrder
    }

    // Update in order history
    const historyIndex = orderHistory.value.findIndex(o => o.id === updatedOrder.id)
    if (historyIndex !== -1) {
      orderHistory.value[historyIndex] = updatedOrder
    }

    // Update or remove from pending orders based on status
    const pendingIndex = pendingOrders.value.findIndex(o => o.id === updatedOrder.id)
    if (updatedOrder.status === 'pending') {
      if (pendingIndex >= 0) {
        pendingOrders.value[pendingIndex] = updatedOrder
      } else {
        pendingOrders.value.unshift(updatedOrder)
      }
    } else if (pendingIndex >= 0) {
      // Remove from pending if status is no longer PENDING
      pendingOrders.value.splice(pendingIndex, 1)
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
    // State
    currentOrder,
    orderHistory,
    pendingOrders,
    loading,
    error,
    
    // Computed
    hasCurrentOrder,
    currentOrderId,
    currentOrderStatus,
    hasPendingOrders,
    
    // Actions
    createOrder,
    fetchOrder,
    fetchOrderHistory,
    fetchPendingOrders,
    completeMpesaPayment,
    completeCashPayment,
    checkMpesaPaymentStatus,
    clearCurrentOrder,
    clearError,
  }
})