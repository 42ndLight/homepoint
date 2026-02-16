import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCartStore = defineStore('cart', () => {
  // Load cart from localStorage on init
  const loadFromStorage = () => {
    try {
      const stored = localStorage.getItem('cart_items')
      return stored ? JSON.parse(stored) : []
    } catch (error) {
      console.error('Failed to load cart from storage:', error)
      return []
    }
  }

  // State: items array
  const items = ref(loadFromStorage())

  // Save to localStorage whenever items change
  const saveToStorage = () => {
    try {
      localStorage.setItem('cart_items', JSON.stringify(items.value))
    } catch (error) {
      console.error('Failed to save cart to storage:', error)
    }
  }

  // Helper function to round currency values to 2 decimal places
  const roundCurrency = (value) => {
    return Math.round(value * 100) / 100
  }

  // Getters
  const itemCount = computed(() => {
    // Total items - sum of all quantities (supports decimal units like meters, kg)
    return items.value.reduce((sum, item) => {
      return sum + parseFloat(item.quantity || 0)
    }, 0)
  })

  const subtotal = computed(() => {
    // Sum of (price × quantity) for all items
    const sum = items.value.reduce((sum, item) => {
      const price = parseFloat(item.price || 0)
      const quantity = parseFloat(item.quantity || 0)
      return sum + (price * quantity)
    }, 0)
    return roundCurrency(sum)
  })

  const vat = computed(() => {
    // VAT calculation: subtotal × 0.16 (16%)
    return roundCurrency(subtotal.value * 0.16)
  })

  const total = computed(() => {
    // Total: subtotal + vat
    return roundCurrency(subtotal.value + vat.value)
  })

  // Actions
  const addItem = (variant, quantity = 1) => {
    if (!variant || !variant.id) {
      console.error('Invalid variant provided to addItem')
      return
    }

    const qty = parseFloat(quantity)
    if (isNaN(qty) || qty <= 0) {
      console.error('Invalid quantity provided to addItem')
      return
    }

    const existingIndex = items.value.findIndex(item => item.variant_id === variant.id)

    if (existingIndex >= 0) {
      // Update quantity - supports decimal units (meters, kg, etc.)
      const currentQty = parseFloat(items.value[existingIndex].quantity || 0)
      items.value[existingIndex].quantity = currentQty + qty
    } else {
      // Add new item
      items.value.push({
        variant_id: variant.id,
        product_id: variant.product_id || variant.product?.id,
        sku: variant.sku,
        name: variant.name || variant.product?.name || variant.sku,
        price: parseFloat(variant.price),
        quantity: qty,
        unit_type: variant.unit_type || 'piece',
        attributes: variant.attributes || {},
      })
    }

    saveToStorage()
  }

  const removeItem = (variantId) => {
    const index = items.value.findIndex(item => item.variant_id === variantId)
    if (index >= 0) {
      items.value.splice(index, 1)
      saveToStorage()
    }
  }

  const updateQuantity = (variantId, quantity) => {
    const item = items.value.find(item => item.variant_id === variantId)
    if (item) {
      const qty = parseFloat(quantity)
      if (isNaN(qty) || qty <= 0) {
        // Remove item if quantity is 0 or invalid
        removeItem(variantId)
      } else {
        // Update quantity - supports decimal units (meters, kg, etc.)
        item.quantity = qty
        saveToStorage()
      }
    }
  }

  const clearCart = () => {
    items.value = []
    saveToStorage()
  }

  return {
    // State
    items,
    // Getters
    itemCount,
    subtotal,
    vat,
    total,
    // Actions
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
  }
})

