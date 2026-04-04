import api from './api'

class TransactionService {
  /**
   * Fetch all orders with optional filters
   * @param {Object} params - Query parameters (search, start_date, end_date, limit, offset, status)
   * @returns {Promise<Object>} Paginated orders data
   */
  static async getOrders(params = {}) {
    try {
      const queryParams = new URLSearchParams()
      if (params.search) queryParams.append('search', params.search)
      if (params.start_date) queryParams.append('start_date', params.start_date)
      if (params.end_date) queryParams.append('end_date', params.end_date)
      if (params.status) queryParams.append('status', params.status)
      if (params.limit) queryParams.append('limit', params.limit || 20)
      if (params.offset) queryParams.append('offset', params.offset || 0)

      const queryString = queryParams.toString()
      const endpoint = `/orders/orders/${queryString ? '?' + queryString : ''}`

      const data = await api.get(endpoint)
      return data
    } catch (error) {
      console.error('Failed to fetch orders:', error)
      throw error
    }
  }

  /**
   * Get a specific order by ID
   * @param {number} orderId - Order ID
   * @returns {Promise<Object>} Order details
   */
  static async getOrderById(orderId) {
    try {
      const data = await api.get(`/orders/orders/${orderId}/`)
      return data
    } catch (error) {
      console.error(`Failed to fetch order ${orderId}:`, error)
      throw error
    }
  }

  /**
   * Delete an order (soft delete or hard delete depending on backend)
   * @param {number} orderId - Order ID to delete
   * @param {string} reason - Optional reason for deletion
   * @returns {Promise<Object>} Response from backend
   */
  static async deleteOrder(orderId, reason = '') {
    try {
      const data = await api.delete(`/orders/orders/${orderId}/`)
      return data
    } catch (error) {
      console.error(`Failed to delete order ${orderId}:`, error)
      throw error
    }
  }

  /**
   * Filter orders by date range
   * @param {string} startDate - Start date in YYYY-MM-DD format
   * @param {string} endDate - End date in YYYY-MM-DD format
   * @param {Object} additionalParams - Additional query parameters
   * @returns {Promise<Object>} Filtered orders
   */
  static async getOrdersByDateRange(startDate, endDate, additionalParams = {}) {
    try {
      return await this.getOrders({
        ...additionalParams,
        start_date: startDate,
        end_date: endDate,
      })
    } catch (error) {
      console.error(`Failed to fetch orders for date range ${startDate} to ${endDate}:`, error)
      throw error
    }
  }

  /**
   * Search orders by customer name or phone
   * @param {string} query - Search query (customer name or phone number)
   * @param {Object} additionalParams - Additional query parameters
   * @returns {Promise<Object>} Search results
   */
  static async searchOrders(query, additionalParams = {}) {
    try {
      return await this.getOrders({
        ...additionalParams,
        search: query,
      })
    } catch (error) {
      console.error(`Failed to search orders for "${query}":`, error)
      throw error
    }
  }

  /**
   * Get order status color for UI
   * @param {string} status - Order status
   * @returns {string} Tailwind color class
   */
  static getStatusColor(status) {
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

  /**
   * Format order data for display
   * @param {Object} order - Order object from API
   * @returns {Object} Formatted order
   */
  static formatOrder(order) {
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
}

export default TransactionService
