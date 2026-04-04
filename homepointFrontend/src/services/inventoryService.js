import api from './api'

class InventoryService {
  /**
   * Fetch all inventory items with optional filters and search
   * @param {Object} params - Query parameters (search, limit, offset)
   * @returns {Promise<Object>} Inventory data with paginated results
   */
  static async getInventory(params = {}) {
    try {
      const queryParams = new URLSearchParams()
      if (params.search) queryParams.append('search', params.search)
      if (params.limit) queryParams.append('limit', params.limit)
      if (params.offset) queryParams.append('offset', params.offset)

      const queryString = queryParams.toString()
      const endpoint = `/products/inventory/${queryString ? '?' + queryString : ''}`

      const data = await api.get(endpoint)
      return data
    } catch (error) {
      console.error('Failed to fetch inventory:', error)
      throw error
    }
  }

  /**
   * Get inventory by category
   * @param {number} categoryId - Category ID
   * @param {Object} params - Additional query parameters
   * @returns {Promise<Object>} Inventory items filtered by category
   */
  static async getInventoryByCategory(categoryId, params = {}) {
    try {
      const queryParams = new URLSearchParams()
      queryParams.append('category', categoryId)
      if (params.search) queryParams.append('search', params.search)
      if (params.limit) queryParams.append('limit', params.limit)
      if (params.offset) queryParams.append('offset', params.offset)

      const queryString = queryParams.toString()
      const endpoint = `/products/inventory/${queryString ? '?' + queryString : ''}`

      const data = await api.get(endpoint)
      return data
    } catch (error) {
      console.error(`Failed to fetch inventory for category ${categoryId}:`, error)
      throw error
    }
  }

  /**
   * Update stock quantity for a specific inventory item
   * @param {number} inventoryId - Inventory item ID
   * @param {number} quantity - New quantity value
   * @param {string} notes - Optional notes about the update
   * @returns {Promise<Object>} Updated inventory data
   */
  static async updateStock(inventoryId, quantity, notes = '') {
    try {
      const payload = {
        quantity,
      }
      if (notes) {
        payload.notes = notes
      }

      const data = await api.patch(`/products/inventory/${inventoryId}/`, payload)
      return data
    } catch (error) {
      console.error(`Failed to update stock for inventory ${inventoryId}:`, error)
      throw error
    }
  }

  /**
   * Get inventory item by ID
   * @param {number} inventoryId - Inventory item ID
   * @returns {Promise<Object>} Inventory item details
   */
  static async getInventoryById(inventoryId) {
    try {
      const data = await api.get(`/products/inventory/${inventoryId}/`)
      return data
    } catch (error) {
      console.error(`Failed to fetch inventory ${inventoryId}:`, error)
      throw error
    }
  }

  /**
   * Get stock status (in-stock, low-stock, out-of-stock)
   * @param {number} quantity - Quantity value
   * @param {number} reorderPoint - Reorder threshold (default: 10)
   * @returns {string} Status label
   */
  static getStockStatus(quantity, reorderPoint = 10) {
    if (quantity === 0) return 'out-of-stock'
    if (quantity <= reorderPoint) return 'low-stock'
    return 'in-stock'
  }

  /**
   * Get stock status color for UI
   * @param {string} status - Stock status from getStockStatus()
   * @returns {string} Tailwind color class
   */
  static getStatusColor(status) {
    const colors = {
      'in-stock': 'bg-green-100 text-green-800',
      'low-stock': 'bg-yellow-100 text-yellow-800',
      'out-of-stock': 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }
}

export default InventoryService
