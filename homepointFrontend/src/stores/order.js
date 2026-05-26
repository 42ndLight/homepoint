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
      updateOrderInLists(order)
      return { success: true, order }
    } catch (err) {
      error.value = err.message || 'Failed to fetch order'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const fetchOrderHistory = async (params = {}) => {
    loading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()
      if (params.search) queryParams.append('search', params.search)
      if (params.start_date) queryParams.append('start_date', params.start_date)
      if (params.end_date) queryParams.append('end_date', params.end_date)
      if (params.status) queryParams.append('status', params.status)
      if (params.limit) queryParams.append('limit', params.limit)
      if (params.offset) queryParams.append('offset', params.offset)

      const queryString = queryParams.toString()
      const endpoint = `/orders/orders/${queryString ? '?' + queryString : ''}`

      const response = await api.get(endpoint)
      
      if (Array.isArray(response)) {
        orderHistory.value = response
      } else if (response.results) {
        orderHistory.value = response.results
      } else {
        orderHistory.value = []
      }
      
      return { 
        success: true, 
        orders: orderHistory.value,
        count: response.count || orderHistory.value.length
      }
    } catch (err) {
      error.value = err.message || 'Failed to fetch order history'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const deleteOrder = async (orderId) => {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/orders/orders/${orderId}/`)
      
      // Remove from history and pending lists
      orderHistory.value = orderHistory.value.filter(o => o.id !== orderId)
      pendingOrders.value = pendingOrders.value.filter(o => o.id !== orderId)
      
      if (currentOrder.value?.id === orderId) {
        currentOrder.value = null
      }
      
      return { success: true }
    } catch (err) {
      error.value = err.message || 'Failed to delete order'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const fetchPendingOrders = async () => {
    const result = await fetchOrderHistory()
    if (result.success) {
      pendingOrders.value = orderHistory.value.filter(
        (o) => (o.status || '').toLowerCase() === 'pending'
      )
    }
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

  const completeCashPayment = async (order_id, amount = '', transaction_type='') => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(`/payments/cash/`, {
        order_id,
        amount,
        transaction_type,
      })

      // Update order in current and pending lists
      if (response.order_id) {
          updateOrderInLists({ id: response.order_id, ...response });
      }

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
      const response = await api.get(`/payments/check-status/${orderId}/`)
      
      // If payment is successful, refresh the order to update its status in lists
      if (response.status === 'SUCCESS' || response.order_status === 'paid') {
        await fetchOrder(orderId)
        // updateOrderInLists is called inside fetchOrder if currentOrder is updated, 
        // but we should ensure it's updated in all lists.
        const updatedOrder = currentOrder.value
        if (updatedOrder) updateOrderInLists(updatedOrder)
      }

      return {
        success: true,
        status: response.status,
        message: response.status === 'SUCCESS' ? 'Payment confirmed!' : `Current status: ${response.status}`,
        order_status: response.order_status
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

  const initiateStkPush = async (orderId, phoneNumber) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/payments/initiate-stk-push/', {
        order_id: orderId,
        phone_number: phoneNumber,
      })

      return {
        success: true,
        message: response.message,
        checkout_request_id: response.checkout_request_id,
        is_duplicate: response.is_duplicate,
      }
    } catch (err) {
      error.value = err.data?.error || err.message || 'Failed to initiate STK Push'
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

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      shipped: 'bg-blue-100 text-blue-800',
      delivered: 'bg-green-100 text-green-800',
      processing: 'bg-blue-100 text-blue-800',
    }
    return colors[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
  }

  const formatOrder = (order) => {
    if (!order) return null
    return {
      ...order,
      formattedDate: new Date(order.created_at).toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      }),
      formattedTime: new Date(order.created_at).toLocaleTimeString('en-KE', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      formattedAmount: new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(order.total_amount || 0),
    }
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
    deleteOrder,
    initiateStkPush,
    clearCurrentOrder,
    clearError,
    
    // UI Helpers
    getStatusColor,
    formatOrder
  }
})
