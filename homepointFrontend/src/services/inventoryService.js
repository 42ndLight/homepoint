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
      const endpoint = `/products/inventory/`

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
   * @param {number} changeAmount - New quantity value
   *  @param {number} movementType
   * @param {string} notes - Optional notes about the update
   * @returns {Promise<Object>} Updated inventory data
   */
  static async updateStock(inventoryId, changeAmount, movementType, reason = '') {
    try {
      const payload = {
        change_amount: changeAmount, // Matches backend key
        movement_type: movementType, // 'IN' or 'OUT'
        reason: reason
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
   * Upload images for a product or variant
   * @param {File[]} files - Array of image files
   * @param {string} modelType - 'product' or 'variant'
   * @param {number} targetId - The ID of the product or variant
   */
  static async uploadImages(files, modelType, targetId) {
    try {
      // Step 1: Get presigned URLs
      const filenames = Array.from(files).map(f => f.name)
      const presignResponse = await api.post('/products/presignurl/', {
        filenames,
        model_type: modelType,
        target_id: targetId
      })

      const uploadResults = []
      const uploadedKeys = []

      // Step 2: Upload files directly to S3
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const presignData = presignResponse.uploads.find(u => u.original_name === file.name)
        
        if (!presignData) continue

        const response = await fetch(presignData.upload_url, {
          method: 'PUT',
          body: file,
          headers: {
            'Content-Type': file.type
          }
        })

        if (!response.ok) {
          throw new Error(`Failed to upload ${file.name} to S3`)
        }

        uploadedKeys.push(presignData.target_key)
      }

      // Step 3: Finalize upload on backend
      const finalizeResponse = await api.post('/products/invupload/', {
        keys: uploadedKeys,
        model_type: modelType,
        target_id: targetId
      })

      return finalizeResponse
    } catch (error) {
      console.error('Image upload failed:', error)
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
   * Format timestamp to readable date string
   * @param {string} timestamp - ISO timestamp string
   * @returns {string} Formatted date string
   */
  static formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
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
