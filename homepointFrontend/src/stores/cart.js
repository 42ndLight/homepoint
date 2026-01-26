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

  const items = ref(loadFromStorage())

  // Save to localStorage whenever items change
  const saveToStorage = () => {
    try {
      localStorage.setItem('cart_items', JSON.stringify(items.value))
    } catch (error) {
      console.error('Failed to save cart to storage:', error)
    }
  }

  // Computed properties
  const itemCount = computed(() => {
    return items.value.reduce((sum, item) => sum + parseFloat(item.quantity || 0), 0)
  })

  const subtotal = computed(() => {
    return items.value.reduce((sum, item) => {
      const price = parseFloat(item.price || 0)
      const quantity = parseFloat(item.quantity || 0)
      return sum + (price * quantity)
    }, 0)
  })

  const vat = computed(() => {
    return subtotal.value * 0.16 // 16% VAT
  })

  const total = computed(() => {
    return subtotal.value + vat.value
  })

  // Actions
  const addItem = (variant, quantity = 1) => {
    const existingIndex = items.value.findIndex(item => item.variant_id === variant.id)

    if (existingIndex >= 0) {
      // Update quantity
      items.value[existingIndex].quantity = parseFloat(items.value[existingIndex].quantity) + parseFloat(quantity)
    } else {
      // Add new item
      items.value.push({
        variant_id: variant.id,
        product_id: variant.product_id,
        sku: variant.sku,
        name: variant.name || variant.sku, // Fallback to SKU if name not available
        price: parseFloat(variant.price),
        quantity: parseFloat(quantity),
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
      if (qty > 0) {
        item.quantity = qty
        saveToStorage()
      } else {
        removeItem(variantId)
      }
    }
  }

  const clearCart = () => {
    items.value = []
    saveToStorage()
  }

  const getItem = (variantId) => {
    return items.value.find(item => item.variant_id === variantId)
  }

  return {
    items,
    itemCount,
    subtotal,
    vat,
    total,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    getItem,
  }
})

